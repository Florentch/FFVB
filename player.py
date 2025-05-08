import pandas as pd
import numpy as np

from config import SKILL_EVAL_MAPPINGS, SET_MOMENTS

class Player:
    """
    Représente un joueur de volleyball avec ses informations et statistiques.
    
    Cette classe centralise toutes les opérations liées aux données d'un joueur,
    y compris le filtrage des actions et le calcul des statistiques.
    """

    def __init__(self, id_, first_name, last_name, number, df, post=None, team=None):
        """
        Initialise un nouvel objet Player avec les informations de base du joueur.
        """
        self.id = id_
        self.first_name = first_name
        self.last_name = last_name
        self.number = number
        self.post = post
        self.team = team
        self.df = df

    def get_action_df(self, skill, set_moment="Tout", match_filter=None, set_filter = None):
        """
        Filtre les actions du joueur selon plusieurs critères.
        """
        df = self.df[self.df['skill'] == skill].copy()

        if match_filter:
            if not isinstance(match_filter, list):
                match_filter = [match_filter]
            df = df[df['match_id'].isin(match_filter)]

        # Application du filtre set_moment seulement s'il n'est pas "Tout"
        if set_moment != "Tout" and set_moment in SET_MOMENTS:
            if set_moment == "0-10":
                df = df[(df['home_team_score'] <= 10) | (df['visiting_team_score'] <= 10)]
            elif set_moment == "10-20":
                df = df[((df['home_team_score'] > 10) & (df['home_team_score'] < 20)) |
                        ((df['visiting_team_score'] > 10) & (df['visiting_team_score'] < 20))]
            elif set_moment == "20+":
                df = df[(df['home_team_score'] >= 20) | (df['visiting_team_score'] >= 20)]

        if set_filter is not None:
            if isinstance(set_filter, (list, tuple, set)):
                df = df[df['set_number'].isin(set_filter)]
            else:
                df = df[df['set_number'] == set_filter]

        return df

    def get_skill_stats(self, skill, set_moment="Tout", match_filter=None, set_filter = None):
        """
        Calcule les statistiques pour une compétence spécifique du joueur.
        
        Récupère les actions filtrées et calcule les statistiques basées sur
        les évaluations définies dans SKILL_EVAL_MAPPINGS.
        """
        df = self.get_action_df(skill, set_moment, match_filter, set_filter)
        total = len(df)

        mapping = SKILL_EVAL_MAPPINGS.get(skill)
        if mapping is None:
            raise ValueError(f"Aucune évaluation définie pour la compétence : {skill}")

        if total == 0:
            sample = self.compute_skill_stats(df, mapping)
            return {key: 0 for key in sample.keys()}

        return self.compute_skill_stats(df, mapping)

    def get_skill_percentages(self, skill, set_moment="Tout", match_filter=None, set_filter = None):
        """
        Extrait uniquement les pourcentages des statistiques d'une compétence.
        
        Cette méthode est un raccourci pour obtenir uniquement les statistiques
        en pourcentage, sans les valeurs absolues.
        """
        stats = self.get_skill_stats(skill, set_moment, match_filter)
        return {k: v for k, v in stats.items() if k.startswith('%')}

    def get_skill_efficiency(self, skill, set_moment="Tout", match_filter=None, set_filter=None):
        """
        Calcule l'efficacité pour une compétence spécifique.
        
        L'efficacité est calculée comme le ratio entre les points marqués (deux premiers symboles
        dans le mapping d'évaluation) et les fautes (deux derniers symboles dans le mapping).
        
        Returns:
            float: Pourcentage d'efficacité ou None si aucune action n'est disponible
        """
        df = self.get_action_df(skill, set_moment, match_filter, set_filter)
        if df.empty:
            return 0.0
            
        mapping = SKILL_EVAL_MAPPINGS.get(skill)
        if mapping is None or len(mapping) < 4:
            raise ValueError(f"Pas assez de symboles d'évaluation pour la compétence : {skill}")
            
        # Obtenir les symboles dans l'ordre du dictionnaire
        symbols = list(mapping.keys())
        
        # Les deux premiers symboles (points marqués) et les deux derniers (fautes)
        positive_symbols = symbols[:2]
        negative_symbols = symbols[-2:]
        
        # Compter les actions positives et négatives
        positives = df[df['evaluation_code'].isin(positive_symbols)].shape[0]
        negatives = df[df['evaluation_code'].isin(negative_symbols)].shape[0]
        
        # Éviter la division par zéro
        if negatives == 0:
            if positives == 0:
                return 0.0  # Si pas de positif ni négatif, l'efficacité est 0
            else:
                return 100.0  # Si positif mais pas de négatif, l'efficacité est 100%
        
        # Calculer l'efficacité en pourcentage
        efficiency = (positives / negatives) * 100
        
        return round(efficiency, 1)

    @staticmethod
    def compute_skill_stats(df, eval_mapping):
        """
        Calcule les statistiques à partir d'un DataFrame d'actions et d'un mapping d'évaluation.
        
        Cette méthode statique effectue le calcul des statistiques brutes et des pourcentages
        en se basant sur les codes d'évaluation présents dans le DataFrame et 
        leur correspondance dans le mapping fourni.
        """
        total = len(df)
        stats = {'Total': total}

        label_counts = {}
        symbol_counts = df['evaluation_code'].value_counts()

        for symbol, label in eval_mapping.items():
            count = symbol_counts.get(symbol, 0)
            label_counts[label] = label_counts.get(label, 0) + count

        stats.update(label_counts)

        for label, count in label_counts.items():
            stats[f"% {label}"] = round((count / total) * 100, 1) if total else 0.0

        # Ajouter le calcul d'efficacité
        if total > 0 and len(eval_mapping) >= 4:
            symbols = list(eval_mapping.keys())
            positive_symbols = symbols[:2]
            negative_symbols = symbols[-2:]
            
            positives = sum(symbol_counts.get(symbol, 0) for symbol in positive_symbols)
            negatives = sum(symbol_counts.get(symbol, 0) for symbol in negative_symbols)
            
            if negatives == 0:
                stats['% Efficacité'] = 1.0 if positives > 0 else 0.0
            else:
                stats['% Efficacité'] = round((positives / negatives), 1)
        else:
            stats['% Efficacité'] = 0.0

        return stats

    @classmethod
    def get_skill_labels(cls, with_percent=True):
        """
        Récupère tous les libellés d'évaluation disponibles pour chaque compétence.
        
        Cette méthode de classe analyse les mappings d'évaluation et retourne
        une structure contenant les différents libellés d'évaluation pour chaque
        compétence, avec ou sans le préfixe '%'.
        """
        labels = {}
        for skill, symbol_map in SKILL_EVAL_MAPPINGS.items():
            seen = set()
            ordered_vals = []
            for val in symbol_map.values():
                if val not in seen:
                    ordered_vals.append(val)
                    seen.add(val)
            skill_labels = [f"% {v}" if with_percent else v for v in ordered_vals]
            # Ajouter l'efficacité
            if with_percent and len(symbol_map) >= 4:
                skill_labels.append("% Efficacité")
            labels[skill] = skill_labels
        return labels

    def get_full_name(self):
        """
        Retourne le nom complet du joueur
        """
        return f"{self.first_name} {self.last_name}"

    def get_display_name(self):
        """
        Retourne le nom d'affichage complet du joueur avec son numéro
        """
        return f"{self.number} – {self.last_name} {self.first_name}"

    def get_matches(self):
        """
        Retourne la liste des identifiants de matchs auxquels le joueur a participé
        """
        if self.df is None or self.df.empty:
            return []
        return self.df['match_id'].dropna().unique().tolist()

    def get_match_info(self, match_id):
        """
        Retourne les informations basiques sur un match
        """
        if self.df is None or self.df.empty:
            return None
            
        match_rows = self.df[self.df['match_id'] == match_id]
        if match_rows.empty:
            return None
            
        row = match_rows.iloc[0]
        return {
            'match_id': match_id,
            'match_day': row.get('match_day', ''),
            'home_team': row.get('home_team', 'Équipe A'),
            'visiting_team': row.get('visiting_team', 'Équipe B')
        }