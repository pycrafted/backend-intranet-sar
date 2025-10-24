#!/usr/bin/env python3
"""
Service de messages de chargement intelligents pour le chatbot
"""

import random
import time
from typing import List, Dict, Optional

class LoadingMessageService:
    """Service pour générer des messages de chargement contextuels"""
    
    def __init__(self):
        self.messages = {
            'searching': [
                "🔍 Recherche dans la base de connaissances...",
                "📚 Consultation des documents SAR...",
                "🧠 Analyse de votre question...",
                "⚡ Traitement en cours...",
                "📖 Parcours de la documentation...",
                "🔎 Exploration des données...",
                "💡 Recherche de la meilleure réponse...",
                "📋 Vérification des informations...",
                "🎯 Identification de la solution...",
                "📊 Analyse des données SAR...",
            ],
            'processing': [
                "⚙️ Traitement de votre demande...",
                "🔄 Génération de la réponse...",
                "📝 Préparation de l'information...",
                "✨ Finalisation de la réponse...",
                "🎨 Mise en forme des données...",
                "📤 Assemblage de la réponse...",
                "🔧 Optimisation du contenu...",
                "📋 Structuration de l'information...",
                "🎯 Personnalisation de la réponse...",
                "💫 Finalisation en cours...",
            ],
            'contextual': {
                'directeur': [
                    "👔 Recherche d'informations sur la direction...",
                    "🏢 Consultation de l'organigramme...",
                    "👤 Identification du dirigeant...",
                    "📋 Vérification des données de direction...",
                ],
                'produit': [
                    "🛢️ Analyse des produits SAR...",
                    "⚗️ Consultation des spécifications...",
                    "📊 Vérification des données techniques...",
                    "🔬 Analyse des caractéristiques...",
                ],
                'processus': [
                    "⚙️ Analyse des processus SAR...",
                    "🔄 Consultation des procédures...",
                    "📋 Vérification des étapes...",
                    "🎯 Identification des méthodes...",
                ],
                'sécurité': [
                    "🛡️ Consultation des protocoles de sécurité...",
                    "⚠️ Vérification des mesures de protection...",
                    "🔒 Analyse des procédures sécuritaires...",
                    "📋 Contrôle des normes de sécurité...",
                ],
                'environnement': [
                    "🌱 Consultation des données environnementales...",
                    "♻️ Analyse des mesures écologiques...",
                    "🌍 Vérification des politiques vertes...",
                    "📊 Contrôle des indicateurs environnementaux...",
                ],
                'qualité': [
                    "⭐ Analyse des standards de qualité...",
                    "📊 Consultation des indicateurs qualité...",
                    "🎯 Vérification des processus qualité...",
                    "📋 Contrôle des certifications...",
                ],
                'technique': [
                    "🔧 Analyse des aspects techniques...",
                    "⚙️ Consultation des spécifications...",
                    "📊 Vérification des données techniques...",
                    "🎯 Identification des solutions...",
                ],
                'général': [
                    "📚 Consultation de la documentation...",
                    "🔍 Recherche d'informations pertinentes...",
                    "💡 Analyse de votre demande...",
                    "📋 Vérification des données disponibles...",
                ]
            }
        }
    
    def get_loading_message(self, question: str = "", phase: str = "searching") -> str:
        """
        Génère un message de chargement contextuel basé sur la question
        
        Args:
            question: La question de l'utilisateur
            phase: Phase du traitement ('searching' ou 'processing')
        
        Returns:
            Message de chargement approprié
        """
        question_lower = question.lower()
        
        # Déterminer le contexte de la question
        context = self._detect_context(question_lower)
        
        # Sélectionner le type de messages approprié
        if context in self.messages['contextual']:
            message_pool = self.messages['contextual'][context]
        else:
            message_pool = self.messages['contextual']['général']
        
        # Ajouter les messages de phase
        if phase == "processing":
            message_pool = self.messages['processing']
        elif phase == "searching":
            message_pool = self.messages['searching']
        
        # Sélectionner un message aléatoire
        return random.choice(message_pool)
    
    def _detect_context(self, question: str) -> str:
        """
        Détecte le contexte de la question pour personnaliser le message
        
        Args:
            question: Question en minuscules
        
        Returns:
            Contexte détecté
        """
        # Mots-clés pour chaque contexte
        context_keywords = {
            'directeur': ['directeur', 'dg', 'pdg', 'dirigeant', 'chef', 'responsable', 'gestionnaire'],
            'produit': ['produit', 'kérosène', 'kerosene', 'carburant', 'fuel', 'gazole', 'essence'],
            'processus': ['processus', 'procédure', 'étape', 'méthode', 'technique', 'opération'],
            'sécurité': ['sécurité', 'sécuritaire', 'protection', 'risque', 'danger', 'accident'],
            'environnement': ['environnement', 'écologique', 'vert', 'pollution', 'déchet', 'recyclage'],
            'qualité': ['qualité', 'standard', 'norme', 'certification', 'contrôle', 'vérification'],
            'technique': ['technique', 'technologie', 'système', 'équipement', 'installation', 'maintenance']
        }
        
        # Compter les occurrences de chaque contexte
        context_scores = {}
        for context, keywords in context_keywords.items():
            score = sum(1 for keyword in keywords if keyword in question)
            if score > 0:
                context_scores[context] = score
        
        # Retourner le contexte avec le score le plus élevé
        if context_scores:
            return max(context_scores, key=context_scores.get)
        
        return 'général'
    
    def get_progressive_messages(self, question: str = "", duration: float = 2.0) -> List[Dict[str, str]]:
        """
        Génère une séquence de messages progressifs pour une durée donnée
        
        Args:
            question: Question de l'utilisateur
            duration: Durée estimée en secondes
        
        Returns:
            Liste de messages avec timing
        """
        messages = []
        
        # Phase de recherche (60% du temps)
        search_duration = duration * 0.6
        search_messages = [
            self.get_loading_message(question, "searching")
            for _ in range(max(1, int(search_duration / 0.5)))
        ]
        
        # Phase de traitement (40% du temps)
        process_duration = duration * 0.4
        process_messages = [
            self.get_loading_message(question, "processing")
            for _ in range(max(1, int(process_duration / 0.5)))
        ]
        
        # Combiner les messages
        all_messages = search_messages + process_messages
        
        # Créer la séquence avec timing
        for i, message in enumerate(all_messages):
            messages.append({
                'message': message,
                'delay': 0.5,  # 500ms entre chaque message
                'phase': 'searching' if i < len(search_messages) else 'processing'
            })
        
        return messages
    
    def get_quick_message(self, question: str = "") -> str:
        """
        Génère un message de chargement rapide pour les réponses courtes
        
        Args:
            question: Question de l'utilisateur
        
        Returns:
            Message de chargement rapide
        """
        quick_messages = [
            "⚡ Recherche rapide...",
            "🔍 Consultation...",
            "📚 Vérification...",
            "💡 Analyse...",
            "🎯 Identification...",
            "📋 Contrôle...",
            "✨ Traitement...",
            "🔄 Génération...",
        ]
        
        return random.choice(quick_messages)
    
    def get_error_message(self, error_type: str = "general") -> str:
        """
        Génère un message d'erreur contextuel
        
        Args:
            error_type: Type d'erreur
        
        Returns:
            Message d'erreur approprié
        """
        error_messages = {
            'general': [
                "❌ Une erreur s'est produite lors de la recherche...",
                "⚠️ Problème de connexion à la base de données...",
                "🔄 Erreur de traitement, nouvelle tentative...",
                "📡 Problème de communication avec le serveur...",
            ],
            'timeout': [
                "⏰ Délai d'attente dépassé...",
                "🕐 La recherche prend plus de temps que prévu...",
                "⏱️ Traitement en cours, veuillez patienter...",
                "🔄 Optimisation de la recherche...",
            ],
            'not_found': [
                "🔍 Aucune information trouvée...",
                "📚 Documentation non disponible...",
                "❓ Question non reconnue...",
                "📋 Aucune correspondance trouvée...",
            ]
        }
        
        return random.choice(error_messages.get(error_type, error_messages['general']))

# Instance globale du service
loading_service = LoadingMessageService()

