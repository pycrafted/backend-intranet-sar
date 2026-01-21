from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from django.db.models import Count, Q, Sum, Avg, F
from django.utils import timezone
from datetime import timedelta, datetime
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from .models import UserLogin, AppMetric
from .serializers import (
    UserLoginSerializer,
    AppMetricSerializer,
    MetricsSummarySerializer
)

User = get_user_model()


class MetricsSummaryView(APIView):
    """
    Vue pour récupérer un résumé complet des métriques
    Accessible uniquement aux administrateurs
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # Vérifier que l'utilisateur est admin
        if not (request.user.is_superuser or getattr(request.user, 'is_admin_group', False)):
            return Response(
                {'error': 'Accès refusé. Administrateur requis.'},
                status=status.HTTP_403_FORBIDDEN
            )

        now = timezone.now()
        today = now.date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        # Connexions par période
        daily_logins = UserLogin.objects.filter(
            login_time__date=today
        ).count()

        weekly_logins = UserLogin.objects.filter(
            login_time__date__gte=week_ago
        ).count()

        monthly_logins = UserLogin.objects.filter(
            login_time__date__gte=month_ago
        ).count()

        # Utilisateurs actifs (qui se sont connectés)
        active_users_today = UserLogin.objects.filter(
            login_time__date=today
        ).values('user').distinct().count()

        active_users_week = UserLogin.objects.filter(
            login_time__date__gte=week_ago
        ).values('user').distinct().count()

        active_users_month = UserLogin.objects.filter(
            login_time__date__gte=month_ago
        ).values('user').distinct().count()

        # Total utilisateurs
        total_users = User.objects.filter(is_active=True).count()

        # Autres métriques (si les apps existent)
        try:
            from actualites.models import Article
            total_articles = Article.objects.count()
        except ImportError:
            total_articles = 0

        try:
            from documents.models import Document
            total_documents = Document.objects.count()
        except ImportError:
            total_documents = 0

        try:
            from forum.models import Post
            total_forum_posts = Post.objects.count()
        except ImportError:
            total_forum_posts = 0

        try:
            from annuaire.models import Employee
            total_employees = Employee.objects.count()
        except ImportError:
            total_employees = 0

        # Tendances des connexions (30 derniers jours)
        login_trend_daily = []
        for i in range(30):
            date = today - timedelta(days=i)
            count = UserLogin.objects.filter(login_time__date=date).count()
            login_trend_daily.append({
                'date': date.isoformat(),
                'count': count
            })
        login_trend_daily.reverse()

        # Tendances hebdomadaires (12 dernières semaines)
        login_trend_weekly = []
        for i in range(12):
            week_start = today - timedelta(weeks=i+1)
            week_end = today - timedelta(weeks=i)
            count = UserLogin.objects.filter(
                login_time__date__gte=week_start,
                login_time__date__lt=week_end
            ).count()
            login_trend_weekly.append({
                'week_start': week_start.isoformat(),
                'week_end': week_end.isoformat(),
                'count': count
            })
        login_trend_weekly.reverse()

        # Tendances mensuelles (12 derniers mois)
        login_trend_monthly = []
        for i in range(12):
            month_start = today.replace(day=1) - timedelta(days=30*i)
            if i == 0:
                month_end = today
            else:
                month_end = month_start + timedelta(days=30)
            count = UserLogin.objects.filter(
                login_time__date__gte=month_start,
                login_time__date__lt=month_end
            ).count()
            login_trend_monthly.append({
                'month_start': month_start.isoformat(),
                'month_end': month_end.isoformat(),
                'count': count
            })
        login_trend_monthly.reverse()

        # Tendances annuelles (5 dernières années)
        login_trend_yearly = []
        for i in range(5):
            year = today.year - i
            year_start = today.replace(year=year, month=1, day=1)
            if i == 0:
                year_end = today
            else:
                year_end = today.replace(year=year+1, month=1, day=1)
            count = UserLogin.objects.filter(
                login_time__date__gte=year_start,
                login_time__date__lt=year_end
            ).count()
            login_trend_yearly.append({
                'year_start': year_start.isoformat(),
                'year_end': year_end.isoformat(),
                'year': year,
                'count': count
            })
        login_trend_yearly.reverse()

        # Top utilisateurs (30 derniers jours)
        top_users_data = UserLogin.objects.filter(
            login_time__date__gte=month_ago
        ).values('user__email', 'user__first_name', 'user__last_name').annotate(
            login_count=Count('id')
        ).order_by('-login_count')[:10]

        top_users = []
        for user_data in top_users_data:
            name = f"{user_data['user__first_name']} {user_data['user__last_name']}".strip()
            if not name:
                name = user_data['user__email']
            top_users.append({
                'email': user_data['user__email'],
                'name': name,
                'login_count': user_data['login_count']
            })

        # Durée moyenne de session (30 derniers jours)
        avg_session_duration = UserLogin.objects.filter(
            login_time__date__gte=month_ago,
            session_duration__isnull=False
        ).aggregate(avg_duration=Avg('session_duration'))['avg_duration']
        
        avg_session_minutes = 0
        if avg_session_duration:
            avg_session_minutes = int(avg_session_duration.total_seconds() / 60)

        # Taux d'engagement
        engagement_rate = 0
        if total_users > 0:
            engagement_rate = round((active_users_month / total_users) * 100, 1)

        # Heures de pointe (moyenne des connexions par heure sur 365 derniers jours)
        # Pour identifier les heures où le serveur est le plus sollicité en moyenne
        hourly_logins = []
        # Calculer la moyenne sur les 365 derniers jours
        year_ago = today - timedelta(days=365)
        days_to_analyze = 365
        for hour in range(24):
            # Compter toutes les connexions à cette heure sur les 365 derniers jours
            total_count = UserLogin.objects.filter(
                login_time__date__gte=year_ago,
                login_time__hour=hour
            ).count()
            # Calculer la moyenne (nombre total / nombre de jours)
            avg_count = round(total_count / days_to_analyze, 1) if days_to_analyze > 0 else 0
            hourly_logins.append({
                'hour': hour,
                'count': int(avg_count),  # Nombre entier pour l'affichage
                'avg_count': avg_count,  # Valeur décimale pour précision
                'total_count': total_count  # Total sur la période pour référence
            })

        # Activité par jour (365 derniers jours)
        weekday_activity = []
        year_ago = today - timedelta(days=365)
        for i in range(365):
            date = today - timedelta(days=i)
            count = UserLogin.objects.filter(login_time__date=date).count()
            weekday_activity.append({
                'day': date.strftime('%A'),
                'day_fr': ['Lundi', 'Mardi', 'Mercredi', 'Jeudi', 'Vendredi', 'Samedi', 'Dimanche'][date.weekday()],
                'date': date.isoformat(),
                'count': count
            })
        weekday_activity.reverse()

        # Répartition par département
        department_stats = UserLogin.objects.filter(
            login_time__date__gte=month_ago
        ).values('user__department__name').annotate(
            login_count=Count('id'),
            unique_users=Count('user', distinct=True)
        ).order_by('-login_count')[:10]

        departments = []
        for dept_data in department_stats:
            departments.append({
                'name': dept_data['user__department__name'] or 'Sans département',
                'login_count': dept_data['login_count'],
                'unique_users': dept_data['unique_users']
            })

        # Documents les plus téléchargés
        top_documents = []
        try:
            from documents.models import Document
            top_docs = Document.objects.filter(
                is_active=True
            ).order_by('-download_count')[:10]
            top_documents = [
                {
                    'title': doc.title,
                    'download_count': doc.download_count,
                    'category': doc.category.name if doc.category else 'Sans catégorie'
                }
                for doc in top_docs
            ]
        except ImportError:
            pass

        # Nouveaux utilisateurs (30 derniers jours)
        new_users_count = User.objects.filter(
            date_joined__date__gte=month_ago
        ).count()

        # Total téléchargements de documents
        total_downloads = 0
        try:
            from documents.models import Document
            from django.db.models import Sum
            total_downloads = Document.objects.filter(
                is_active=True
            ).aggregate(total=Sum('download_count'))['total'] or 0
        except ImportError:
            pass

        data = {
            'daily_logins': daily_logins,
            'weekly_logins': weekly_logins,
            'monthly_logins': monthly_logins,
            'total_users': total_users,
            'active_users_today': active_users_today,
            'active_users_week': active_users_week,
            'active_users_month': active_users_month,
            'total_articles': total_articles,
            'total_documents': total_documents,
            'total_forum_posts': total_forum_posts,
            'total_employees': total_employees,
            'login_trend_daily': login_trend_daily,
            'login_trend_weekly': login_trend_weekly,
            'login_trend_monthly': login_trend_monthly,
            'login_trend_yearly': login_trend_yearly,
            'top_users': top_users,
            # Nouvelles métriques
            'avg_session_duration_minutes': avg_session_minutes,
            'engagement_rate': engagement_rate,
            'hourly_logins': hourly_logins,
            'weekday_activity': weekday_activity,
            'department_stats': departments,
            'top_documents': top_documents,
            'new_users_count': new_users_count,
            'total_downloads': total_downloads,
        }

        serializer = MetricsSummarySerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserLoginListView(generics.ListAPIView):
    """
    Liste des connexions utilisateurs avec filtrage
    """
    serializer_class = UserLoginSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if not (self.request.user.is_superuser or getattr(self.request.user, 'is_admin_group', False)):
            # Les non-admins voient seulement leurs propres connexions
            return UserLogin.objects.filter(user=self.request.user)
        
        queryset = UserLogin.objects.select_related('user', 'user__department').all()
        
        # Filtrage par utilisateur
        user_id = self.request.query_params.get('user_id', None)
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        # Filtrage par date
        date_from = self.request.query_params.get('date_from', None)
        date_to = self.request.query_params.get('date_to', None)
        
        if date_from:
            queryset = queryset.filter(login_time__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(login_time__date__lte=date_to)
        
        return queryset.order_by('-login_time')


class LoginStatsView(APIView):
    """
    Vue pour récupérer des statistiques détaillées sur les connexions
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not (request.user.is_superuser or getattr(request.user, 'is_admin_group', False)):
            return Response(
                {'error': 'Accès refusé. Administrateur requis.'},
                status=status.HTTP_403_FORBIDDEN
            )

        period = request.query_params.get('period', 'daily')  # daily, weekly, monthly
        
        now = timezone.now()
        today = now.date()
        
        if period == 'daily':
            # 30 derniers jours
            stats = []
            for i in range(30):
                date = today - timedelta(days=i)
                count = UserLogin.objects.filter(login_time__date=date).count()
                unique_users = UserLogin.objects.filter(
                    login_time__date=date
                ).values('user').distinct().count()
                stats.append({
                    'date': date.isoformat(),
                    'logins': count,
                    'unique_users': unique_users
                })
            stats.reverse()
            
        elif period == 'weekly':
            # 12 dernières semaines
            stats = []
            for i in range(12):
                week_start = today - timedelta(weeks=i+1)
                week_end = today - timedelta(weeks=i)
                count = UserLogin.objects.filter(
                    login_time__date__gte=week_start,
                    login_time__date__lt=week_end
                ).count()
                unique_users = UserLogin.objects.filter(
                    login_time__date__gte=week_start,
                    login_time__date__lt=week_end
                ).values('user').distinct().count()
                stats.append({
                    'week_start': week_start.isoformat(),
                    'week_end': week_end.isoformat(),
                    'logins': count,
                    'unique_users': unique_users
                })
            stats.reverse()
            
        else:  # monthly
            # 12 derniers mois
            stats = []
            for i in range(12):
                month_start = today.replace(day=1) - timedelta(days=30*i)
                if i == 0:
                    month_end = today
                else:
                    month_end = month_start + timedelta(days=30)
                count = UserLogin.objects.filter(
                    login_time__date__gte=month_start,
                    login_time__date__lt=month_end
                ).count()
                unique_users = UserLogin.objects.filter(
                    login_time__date__gte=month_start,
                    login_time__date__lt=month_end
                ).values('user').distinct().count()
                stats.append({
                    'month_start': month_start.isoformat(),
                    'month_end': month_end.isoformat(),
                    'logins': count,
                    'unique_users': unique_users
                })
            stats.reverse()

        return Response({'period': period, 'stats': stats}, status=status.HTTP_200_OK)
