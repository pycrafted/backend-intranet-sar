import csv
import os
from django.conf import settings
from typing import List, Dict, Optional, Tuple
import re

class MAIService:
    """
    Service MAI (Moteur d'Assistance Intelligent) basé sur le dataset CSV officiel de la SAR.
    Ce service ne répond qu'aux questions concernant les données du dataset sar_official_dataset.csv.
    """
    
    def __init__(self):
        self.dataset_path = os.path.join(settings.BASE_DIR, 'data', 'sar_official_dataset.csv')
        self.qa_pairs = self._load_dataset()
    
    def _load_dataset(self) -> List[Dict[str, str]]:
        """Charge le dataset CSV en mémoire"""
        qa_pairs = []
        
        try:
            with open(self.dataset_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    qa_pairs.append({
                        'question': row['question'].strip(),
                        'answer': row['answer'].strip()
                    })
            
            print(f"✅ [MAI] Dataset chargé: {len(qa_pairs)} questions-réponses")
            return qa_pairs
            
        except FileNotFoundError:
            print(f"❌ [MAI] Fichier dataset non trouvé: {self.dataset_path}")
            return []
        except Exception as e:
            print(f"❌ [MAI] Erreur lors du chargement du dataset: {e}")
            return []
    
    def _normalize_text(self, text: str) -> str:
        """Normalise le texte pour la comparaison (minuscules, suppression accents, etc.)"""
        # Convertir en minuscules
        text = text.lower()
        
        # Supprimer les accents et caractères spéciaux
        replacements = {
            'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'å': 'a',
            'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
            'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
            'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
            'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c', 'ñ': 'n',
            'œ': 'oe', 'æ': 'ae',
            'k': 'k', 'é': 'e'  # kérosène -> kerosene
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        # Normaliser les variations de mots
        text = text.replace('kérosène', 'kerosene')
        text = text.replace('kerozene', 'kerosene')
        text = text.replace('mérox', 'merox')
        text = text.replace('merox', 'merox')
        
        # Supprimer la ponctuation et les espaces multiples
        text = re.sub(r'[^\w\s]', ' ', text)
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _calculate_similarity(self, question1: str, question2: str) -> float:
        """Calcule la similarité entre deux questions (algorithme amélioré)"""
        q1_normalized = self._normalize_text(question1)
        q2_normalized = self._normalize_text(question2)
        
        # Vérification exacte d'abord
        if q1_normalized == q2_normalized:
            return 1.0
        
        # Vérification de contenu (si une question contient l'autre)
        if q1_normalized in q2_normalized or q2_normalized in q1_normalized:
            return 0.9
        
        # Vérification spéciale pour les questions sur les unités
        if 'unite' in q1_normalized and 'unite' in q2_normalized:
            if 'kerosene' in q1_normalized and 'kerosene' in q2_normalized:
                if 'aviation' in q1_normalized and 'aviation' in q2_normalized:
                    return 0.95  # Très forte similarité pour les questions sur l'unité kérosène aviation
        
        # Vérification spéciale pour les questions sur les valeurs (première, deuxième, etc.)
        if 'valeur' in q1_normalized and 'valeur' in q2_normalized:
            if 'premiere' in q1_normalized and 'premiere' in q2_normalized:
                return 0.95
            if 'deuxieme' in q1_normalized and 'deuxieme' in q2_normalized:
                return 0.95
            if 'troisieme' in q1_normalized and 'troisieme' in q2_normalized:
                return 0.95
            if 'quatrieme' in q1_normalized and 'quatrieme' in q2_normalized:
                return 0.95
            if 'cinquieme' in q1_normalized and 'cinquieme' in q2_normalized:
                return 0.95
        
        # Vérification spéciale pour les questions sur les acronymes
        if ('abreviation' in q1_normalized and 'abreviation' in q2_normalized) or \
           ('acronyme' in q1_normalized and 'acronyme' in q2_normalized) or \
           ('signifie' in q1_normalized and 'signifie' in q2_normalized):
            return 0.9
        
        q1_words = set(q1_normalized.split())
        q2_words = set(q2_normalized.split())
        
        if not q1_words or not q2_words:
            return 0.0
        
        # Calcul de la similarité Jaccard
        intersection = len(q1_words.intersection(q2_words))
        union = len(q1_words.union(q2_words))
        
        jaccard_similarity = intersection / union if union > 0 else 0.0
        
        # Bonus pour les mots-clés importants
        important_keywords = [
            # Valeurs fondamentales
            'premiere', 'deuxieme', 'troisieme', 'quatrieme', 'cinquieme', 'valeur', 'fondamentale',
            # Entreprise
            'sar', 'societe', 'africaine', 'raffinage',
            # Valeurs
            'securite', 'integrite', 'ethique', 'equipe', 'responsabilite', 'performance',
            # Dates et événements
            'date', 'inauguration', 'officielle', 'precise', 'annee', 'demarrage',
            # Capacités et production
            'capacite', 'traitement', 'tonnes', 'million', 'barils', 'production',
            # Unités et procédés
            'unite', 'kerosene', 'aviation', 'merox', 'distillation', 'reformage', 'catalytique', 'jet', 'carbureacteur',
            # Produits
            'produits', 'strategiques', 'raffines', 'essence', 'gaz', 'butane', 'fuel', 'gasoil',
            # Acronymes
            'abreviation', 'acronyme', 'signifie', 'arda', 'onas', 'ucg', 'dsi', 'chs', 'ct',
            # Services et directions
            'service', 'direction', 'laboratoire', 'inspection', 'environnement', 'surete',
            # Techniques
            'brut', 'petrole', 'hydrocarbures', 'raffinerie', 'usine', 'installations'
        ]
        q1_important = sum(1 for word in q1_words if word in important_keywords)
        q2_important = sum(1 for word in q2_words if word in important_keywords)
        
        if q1_important > 0 and q2_important > 0:
            keyword_bonus = min(0.4, (q1_important + q2_important) * 0.15)
            jaccard_similarity += keyword_bonus
        
        # Bonus spécial pour les questions sur les valeurs
        if 'valeur' in q1_words and 'valeur' in q2_words:
            jaccard_similarity += 0.2
        if 'premiere' in q1_words and 'premiere' in q2_words:
            jaccard_similarity += 0.2
        
        # Bonus spécial pour les questions sur les dates
        if 'date' in q1_words and 'date' in q2_words:
            jaccard_similarity += 0.3
        if 'inauguration' in q1_words and 'inauguration' in q2_words:
            jaccard_similarity += 0.3
        if 'officielle' in q1_words and 'officielle' in q2_words:
            jaccard_similarity += 0.2
        
        # Bonus spécial pour les questions sur les unités
        if 'unite' in q1_words and 'unite' in q2_words:
            jaccard_similarity += 0.3
        if 'kerosene' in q1_words and 'kerosene' in q2_words:
            jaccard_similarity += 0.4
        if 'aviation' in q1_words and 'aviation' in q2_words:
            jaccard_similarity += 0.4
        if 'merox' in q1_words and 'merox' in q2_words:
            jaccard_similarity += 0.5
        if 'distillation' in q1_words and 'distillation' in q2_words:
            jaccard_similarity += 0.3
        
        # Bonus spécial pour les questions sur les valeurs (première, deuxième, etc.)
        if 'premiere' in q1_words and 'premiere' in q2_words and 'valeur' in q1_words and 'valeur' in q2_words:
            jaccard_similarity += 0.6
        if 'deuxieme' in q1_words and 'deuxieme' in q2_words and 'valeur' in q1_words and 'valeur' in q2_words:
            jaccard_similarity += 0.6
        if 'troisieme' in q1_words and 'troisieme' in q2_words and 'valeur' in q1_words and 'valeur' in q2_words:
            jaccard_similarity += 0.6
        if 'quatrieme' in q1_words and 'quatrieme' in q2_words and 'valeur' in q1_words and 'valeur' in q2_words:
            jaccard_similarity += 0.6
        if 'cinquieme' in q1_words and 'cinquieme' in q2_words and 'valeur' in q1_words and 'valeur' in q2_words:
            jaccard_similarity += 0.6
        
        # Bonus spécial pour les questions sur les acronymes
        if 'abreviation' in q1_words and 'abreviation' in q2_words:
            jaccard_similarity += 0.4
        if 'acronyme' in q1_words and 'acronyme' in q2_words:
            jaccard_similarity += 0.4
        if 'signifie' in q1_words and 'signifie' in q2_words:
            jaccard_similarity += 0.3
        
        # Bonus spécial pour les questions sur les capacités
        if 'capacite' in q1_words and 'capacite' in q2_words:
            jaccard_similarity += 0.3
        if 'tonnes' in q1_words and 'tonnes' in q2_words:
            jaccard_similarity += 0.3
        if 'million' in q1_words and 'million' in q2_words:
            jaccard_similarity += 0.3
        
        # Bonus spécial pour les questions sur les produits
        if 'produits' in q1_words and 'produits' in q2_words:
            jaccard_similarity += 0.3
        if 'strategiques' in q1_words and 'strategiques' in q2_words:
            jaccard_similarity += 0.3
        if 'raffines' in q1_words and 'raffines' in q2_words:
            jaccard_similarity += 0.3
        
        return min(1.0, jaccard_similarity)
    
    def search_answer(self, user_question: str, threshold: float = 0.2) -> Optional[Dict[str, str]]:
        """
        Recherche la meilleure réponse dans le dataset basée sur la question de l'utilisateur.
        
        Args:
            user_question: Question de l'utilisateur
            threshold: Seuil de similarité minimum (0.0 à 1.0)
        
        Returns:
            Dict avec 'question', 'answer' et 'similarity' ou None si aucune correspondance
        """
        if not self.qa_pairs:
            return None
        
        print(f"🔍 [MAI_SEARCH] Question utilisateur: '{user_question}'")
        print(f"🔍 [MAI_SEARCH] Seuil de similarité: {threshold}")
        
        best_match = None
        best_similarity = 0.0
        all_similarities = []
        
        # Rechercher la meilleure correspondance
        for i, qa_pair in enumerate(self.qa_pairs):
            similarity = self._calculate_similarity(user_question, qa_pair['question'])
            all_similarities.append((i, qa_pair['question'], similarity))
            
            if similarity > best_similarity and similarity >= threshold:
                best_similarity = similarity
                best_match = {
                    'question': qa_pair['question'],
                    'answer': qa_pair['answer'],
                    'similarity': similarity
                }
                print(f"✅ [MAI_SEARCH] Nouvelle meilleure correspondance: {similarity:.3f} - '{qa_pair['question']}'")
        
        # Afficher les 5 meilleures similarités pour debug
        all_similarities.sort(key=lambda x: x[2], reverse=True)
        print(f"🔍 [MAI_SEARCH] Top 5 similarités:")
        for i, (idx, question, sim) in enumerate(all_similarities[:5]):
            print(f"  {i+1}. {sim:.3f} - '{question}'")
        
        print(f"🔍 [MAI_SEARCH] Meilleure correspondance finale: {best_similarity:.3f}")
        
        return best_match
    
    def get_all_questions(self) -> List[str]:
        """Retourne toutes les questions du dataset"""
        return [qa['question'] for qa in self.qa_pairs]
    
    def get_question_count(self) -> int:
        """Retourne le nombre total de questions dans le dataset"""
        return len(self.qa_pairs)
    
    def is_question_about_sar(self, question: str) -> bool:
        """
        Vérifie si la question concerne la SAR en cherchant des mots-clés spécifiques.
        Cette méthode aide à déterminer si la question est dans le domaine du dataset.
        """
        sar_keywords = [
            # Entreprise et identité
            'sar', 'societe africaine de raffinage', 'raffinerie', 'entreprise', 'organisation', 'compagnie',
            # Localisation
            'sangomar', 'mbao', 'dakar', 'senegal', 'afrique', 'ouest',
            # Produits pétroliers
            'petrole', 'brut', 'carburant', 'essence', 'gaz butane', 'gasoil', 'fuel', 'jet a-1', 'kerosene',
            'hydrocarbures', 'produits', 'raffines', 'strategiques',
            # Procédés techniques
            'distillation', 'reformage', 'merox', 'catalytique', 'unite', 'aviation', 'jet', 'carbureacteur',
            # Capacités et production
            'capacite', 'traitement', 'tonnes', 'million', 'barils', 'production', 'commercialisation',
            # Valeurs fondamentales
            'valeur', 'fondamentale', 'premiere', 'deuxieme', 'troisieme', 'quatrieme', 'cinquieme',
            'securite', 'integrite', 'ethique', 'equipe', 'responsabilite', 'performance',
            # Dates et événements
            'date', 'inauguration', 'officielle', 'precise', 'annee', 'demarrage', '1964', '1963',
            # Services et directions
            'service', 'direction', 'laboratoire', 'inspection', 'environnement', 'surete', 'dsi', 'rh',
            # Partenaires et acronymes
            'woodside', 'petrosen', 'senelec', 'technip', 'arda', 'onas', 'ucg', 'chs', 'ct',
            # Qualité et certification
            'qualite', 'iso', 'certification', 'normes', 'conformite',
            # Modernisation et projets
            'modernisation', 'projet', 'sar 2.0', 'petrochimie', 'digitalisation'
        ]
        
        question_lower = self._normalize_text(question)
        
        # Vérifier si au moins un mot-clé SAR est présent
        for keyword in sar_keywords:
            if keyword in question_lower:
                return True
        
        # Si la question contient "SAR" ou "société africaine", c'est automatiquement valide
        if 'sar' in question_lower or 'societe africaine' in question_lower:
            return True
        
        return False
    
    def get_context_for_question(self, user_question: str) -> str:
        """
        Génère un contexte pour la question de l'utilisateur basé sur le dataset.
        Utilisé pour alimenter l'IA avec des informations pertinentes.
        """
        # Chercher la meilleure réponse
        best_match = self.search_answer(user_question, threshold=0.2)
        
        if best_match:
            context = f"Question similaire trouvée: {best_match['question']}\n"
            context += f"Réponse officielle: {best_match['answer']}\n"
            context += f"Similarité: {best_match['similarity']:.2f}"
            return context
        
        # Si aucune correspondance directe, chercher des questions liées
        related_questions = []
        for qa_pair in self.qa_pairs:
            similarity = self._calculate_similarity(user_question, qa_pair['question'])
            if 0.1 <= similarity < 0.3:  # Similarité faible mais présente
                related_questions.append({
                    'question': qa_pair['question'],
                    'answer': qa_pair['answer'],
                    'similarity': similarity
                })
        
        if related_questions:
            # Trier par similarité et prendre les 3 meilleures
            related_questions.sort(key=lambda x: x['similarity'], reverse=True)
            context = "Questions liées trouvées dans le dataset SAR:\n\n"
            for i, qa in enumerate(related_questions[:3], 1):
                context += f"{i}. {qa['question']}\n"
                context += f"   Réponse: {qa['answer']}\n\n"
            return context
        
        return "Aucune information pertinente trouvée dans le dataset officiel de la SAR."


# Instance globale du service
mai_service = MAIService()
