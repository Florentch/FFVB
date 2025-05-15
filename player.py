import pandas as pd
import numpy as np

from config import EFFICIENCY_CALCULATION, ERROR_CALCULATION, SPECIAL_METRICS, SET_MOMENTS, SKILL_EVAL_MAPPINGS

class Player:
    """
    Représente un joueur de volleyball avec ses informations et statistiques.
    """

    def __init__(self, id_, first_name, last_name, number, df, df_prev=None, df_next=None, post=None, team=None):
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
        self.df_prev = df_prev 
        self.df_next = df_next

    def get_action_df(self, skill, set_moment="Tout", match_filter=None, set_filter=None):
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

    def get_skill_stats(self, skill, set_moment="Tout", match_filter=None, set_filter=None):
        """
        Calcule les statistiques pour une compétence spécifique du joueur.
        """
        df = self.get_action_df(skill, set_moment, match_filter, set_filter)
        total = len(df)

        mapping = SKILL_EVAL_MAPPINGS.get(skill)
        if mapping is None:
            raise ValueError(f"Aucune évaluation définie pour la compétence : {skill}")

        if total == 0:
            sample = self.compute_skill_stats(df, mapping)
            return {key: 0 for key in sample.keys()}

        stats = self.compute_skill_stats(df, mapping)
        
        # Calcul des métriques spécifiques pour les passes
        if skill == "Set":
            # Calculer FSO et SO pour les passes
            fso_stats = self.calculate_set_fso(set_moment, match_filter, set_filter)
            so_stats = self.calculate_set_so(set_moment, match_filter, set_filter)
            stats["% FSO"] = fso_stats["% FSO"]
            stats["% SO"] = so_stats["% SO"]
        
        return stats

    def get_skill_percentages(self, skill, set_moment="Tout", match_filter=None, set_filter=None):
        """
        Extrait uniquement les pourcentages des statistiques d'une compétence.
        """
        stats = self.get_skill_stats(skill, set_moment, match_filter, set_filter)
        return {k: v for k, v in stats.items() if k.startswith('%')}

    def get_skill_efficiency(self, skill, set_moment="Tout", match_filter=None, set_filter=None):
        """
        Calcule l'efficacité pour une compétence spécifique.
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
            return 100.0 if positives > 0 else 0.0
        
        # Calculer l'efficacité en pourcentage
        return round((positives / negatives) * 100, 1)

    @staticmethod
    def compute_skill_stats(df, eval_mapping):
        """
        Calcule les statistiques à partir d'un DataFrame d'actions et d'un mapping d'évaluation.
        """
        total = len(df)
        stats = {'Total': total}
        
        # Pas de données à traiter
        if total == 0:
            return {key: 0 for key in ['Total', '% Efficacité', '% Kill', '% Erreur', '% Parfaite', 
                                       '% Ace', '% Positif', '% /', '% Faute', '% Jouable']}
        
        # Obtenir la compétence à partir du DataFrame
        skill = df['skill'].iloc[0] if not df.empty else None
        
        # Compter les occurrences de chaque symbole
        symbol_counts = df['evaluation_code'].value_counts()
        
        # Initialiser les compteurs pour les formules
        symbols = list(eval_mapping.keys())
        symbols_data = {
            "symbols_first": symbol_counts.get(symbols[0], 0) if symbols else 0,
            "symbols_first_two": sum(symbol_counts.get(symbol, 0) for symbol in symbols[:2]) if len(symbols) >= 2 else 0,
            "symbols_last": symbol_counts.get(symbols[-1], 0) if symbols else 0,
            "symbols_last_two": sum(symbol_counts.get(symbol, 0) for symbol in symbols[-2:]) if len(symbols) >= 2 else 0,
            "symbols_specific": {symbol: symbol_counts.get(symbol, 0) for symbol in symbols}
        }
        
        # Calculer les métriques de base (comptes par type)
        label_counts = {}
        for symbol, label in eval_mapping.items():
            count = symbol_counts.get(symbol, 0)
            label_counts[label] = label_counts.get(label, 0) + count
        
        stats.update(label_counts)
        
        # Calculer les pourcentages pour chaque libellé
        for label, count in label_counts.items():
            stats[f"% {label}"] = round((count / total) * 100, 1) if total else 0.0
        
        # Calculer l'efficacité si la formule existe
        if skill and skill in EFFICIENCY_CALCULATION:
            numerator = _calculate_efficiency_numerator(symbols_data, EFFICIENCY_CALCULATION[skill]["formula"])
            stats['% Efficacité'] = round((numerator / total) * 100, 1) if total else 0.0
        else:
            stats['% Efficacité'] = 0.0
        
        # Calculer les erreurs
        if skill and skill in ERROR_CALCULATION:
            error_count = _calculate_error_count(symbols_data, ERROR_CALCULATION[skill])
            stats['% Erreur'] = round((error_count / total) * 100, 1) if total else 0.0
            
            # Pour Set, ajouter aussi % Faute qui est synonyme de % Erreur
            if skill == "Set":
                stats['% Faute'] = stats['% Erreur']
        else:
            stats['% Erreur'] = 0.0
        
        # Calculer les métriques spéciales pour cette compétence
        if skill and skill in SPECIAL_METRICS:
            for metric_name, metric_formula in SPECIAL_METRICS[skill].items():
                if not metric_formula:  # Skip empty formulas
                    stats[metric_name] = 0.0
                    continue
                    
                try:
                    result = _evaluate_metric_formula(metric_formula, symbols_data)
                    stats[metric_name] = round((result / total) * 100, 1) if total else 0.0
                except Exception:
                    stats[metric_name] = 0.0
        
        return stats

    @classmethod
    def get_skill_labels(cls, with_percent=True):
        """
        Récupère tous les libellés d'évaluation disponibles pour chaque compétence.
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

    def calculate_set_fso(self, set_moment="Tout", match_filter=None, set_filter=None, set_type="Tous", attack_type="Tous"):
        """
        Calcule le First Set Order (FSO) pour un passeur.
        """
        # Récupérer les passes filtrées avec le type de passe
        set_df = self._filter_set_df(set_moment, match_filter, set_filter, set_type)
        
        if set_df.empty or self.df_prev is None or self.df_next is None:
            return {"total_fso_situations": 0, "successful_fso": 0, "% FSO": 0.0}
        
        # Collecter les actions de séquence
        result_data = []
        for idx in set_df.index:
            if idx in self.df_prev.index and idx in self.df_next.index:
                prev_action = self.df_prev.loc[idx]
                next_action = self.df_next.loc[idx]
                
                # Filtrer par type d'attaque si nécessaire
                if attack_type != "Tous" and not self._is_valid_attack(next_action, attack_type):
                    continue
                
                result_data.append({
                    'prev_skill': prev_action['skill'],
                    'next_skill': next_action['skill'],
                    'next_evaluation': next_action['evaluation_code']
                })
        
        if not result_data:
            return {"total_fso_situations": 0, "successful_fso": 0, "% FSO": 0.0}
        
        # Créer un DataFrame et filtrer les séquences Réception -> Passe -> Attaque
        combined_df = pd.DataFrame(result_data)
        fso_situations = combined_df[
            (combined_df['prev_skill'] == 'Reception') & 
            (combined_df['next_skill'] == 'Attack')
        ]
        
        total_fso_situations = len(fso_situations)
        if total_fso_situations == 0:
            return {"total_fso_situations": 0, "successful_fso": 0, "% FSO": 0.0}
        
        # Compter les situations avec point marqué
        successful_fso = fso_situations[fso_situations['next_evaluation'] == '#'].shape[0]
        fso_percentage = round((successful_fso / total_fso_situations) * 100, 1)
        
        return {
            "total_fso_situations": total_fso_situations,
            "successful_fso": successful_fso,
            "% FSO": fso_percentage
        }

    def calculate_set_so(self, set_moment="Tout", match_filter=None, set_filter=None, set_type="Tous", attack_type="Tous"):
        """
        Calcule le Set Order (SO) pour un passeur.
        """
        # Récupérer les passes filtrées avec le type de passe
        set_df = self._filter_set_df(set_moment, match_filter, set_filter, set_type)
        
        if set_df.empty or self.df_next is None:
            return {"total_so_situations": 0, "successful_so": 0, "% SO": 0.0}
        
        # Collecter les actions suivantes
        result_data = []
        for idx in set_df.index:
            if idx in self.df_next.index:
                next_action = self.df_next.loc[idx]
                
                # Filtrer par type d'attaque si nécessaire
                if attack_type != "Tous" and not self._is_valid_attack(next_action, attack_type):
                    continue
                
                result_data.append({
                    'next_skill': next_action['skill'],
                    'next_evaluation': next_action['evaluation_code']
                })
        
        if not result_data:
            return {"total_so_situations": 0, "successful_so": 0, "% SO": 0.0}
        
        # Créer un DataFrame et filtrer pour les séquences Passe -> Attaque
        combined_df = pd.DataFrame(result_data)
        so_situations = combined_df[combined_df['next_skill'] == 'Attack']
        
        total_so_situations = len(so_situations)
        if total_so_situations == 0:
            return {"total_so_situations": 0, "successful_so": 0, "% SO": 0.0}
        
        # Compter les situations avec point marqué
        successful_so = so_situations[so_situations['next_evaluation'] == '#'].shape[0]
        so_percentage = round((successful_so / total_so_situations) * 100, 1)
        
        return {
            "total_so_situations": total_so_situations,
            "successful_so": successful_so,
            "% SO": so_percentage
        }

    def get_skill_stats_with_filters(self, skill, set_moment="Tout", match_filter=None, set_filter=None, set_type="Tous", attack_type="Tous"):
        """
        Calcule les statistiques pour une compétence spécifique avec des filtres supplémentaires.
        """
        # Cas 1: Aucun filtre supplémentaire et ce n'est pas une passe
        if (set_type == "Tous" and attack_type == "Tous") and skill != "Set":
            return self.get_skill_stats(skill, set_moment, match_filter, set_filter)
        
        # Récupérer et filtrer les actions
        df = self.get_action_df(skill, set_moment, match_filter, set_filter)
        
        # Filtrer par type de passe si nécessaire
        if set_type != "Tous" and 'set_code' in df.columns:
            df = df[df['set_code'] == set_type]
        
        # Filtrer par type d'attaque pour les passes
        if attack_type != "Tous" and skill == "Set" and self.df_next is not None:
            valid_indices = []
            for idx in df.index:
                if idx in self.df_next.index:
                    next_action = self.df_next.loc[idx]
                    if self._is_valid_attack(next_action, attack_type):
                        valid_indices.append(idx)
            
            if valid_indices:
                df = df.loc[valid_indices]
            else:
                df = df.iloc[0:0]  # DataFrame vide avec la même structure
        
        # Si aucune action ne correspond après les filtres
        if df.empty:
            mapping = SKILL_EVAL_MAPPINGS.get(skill)
            if mapping is None:
                raise ValueError(f"Aucune évaluation définie pour la compétence : {skill}")
            
            sample = self.compute_skill_stats(df, mapping)
            return {key: 0 for key in sample.keys()}
        
        # Calculer les statistiques
        mapping = SKILL_EVAL_MAPPINGS.get(skill)
        if mapping is None:
            raise ValueError(f"Aucune évaluation définie pour la compétence : {skill}")
        
        stats = self.compute_skill_stats(df, mapping)
        
        # Pour les passes, calculer aussi FSO et SO
        if skill == "Set":
            fso_stats = self.calculate_set_fso(set_moment, match_filter, set_filter, set_type, attack_type)
            so_stats = self.calculate_set_so(set_moment, match_filter, set_filter, set_type, attack_type)
            stats["% FSO"] = fso_stats["% FSO"]
            stats["% SO"] = so_stats["% SO"]
        
        return stats
    
    # Méthodes privées d'aide
    
    def _filter_set_df(self, set_moment, match_filter, set_filter, set_type):
        """
        Filtre le DataFrame des passes selon les critères donnés.
        """
        set_df = self.get_action_df("Set", set_moment, match_filter, set_filter)
        
        if set_type != "Tous" and 'set_code' in set_df.columns:
            set_df = set_df[set_df['set_code'] == set_type]
            
        return set_df
    
    def _is_valid_attack(self, action, attack_type):
        """
        Vérifie si une action est une attaque du type spécifié.
        """
        return (action['skill'] == 'Attack' and 
                'attack_code' in action and 
                action['attack_code'] == attack_type)

    @classmethod
    def get_best_players_by_skill(cls, players, skill, set_moment="Tout", match_filter=None, set_filter=None, min_actions=10):
        """
        Retourne le joueur le plus efficace pour une compétence donnée, avec un minimum d'actions requises.
        """
        valid_players = []
        
        for player in players:
            stats = player.get_skill_stats(skill, set_moment, match_filter, set_filter)
            
            # Vérifier si le joueur a suffisamment d'actions
            if stats.get('Total', 0) >= min_actions:
                valid_players.append({
                    'player': player,
                    'efficiency': stats.get('% Efficacité', 0),
                    'total_actions': stats.get('Total', 0)
                })
        
        # Trier les joueurs par efficacité décroissante
        valid_players.sort(key=lambda x: x['efficiency'], reverse=True)
        
        if not valid_players:
            return None
            
        return valid_players[0]


# Fonctions utilitaires

def _calculate_efficiency_numerator(symbols_data, formula):
    """
    Calcule le numérateur pour la formule d'efficacité.
    """
    if formula == "positive_first - negative_last_two":
        return symbols_data["symbols_first"] - symbols_data["symbols_last_two"]
    elif formula == "positive_first_two - negative_last_two":
        return symbols_data["symbols_first_two"] - symbols_data["symbols_last_two"]
    elif formula == "positive_first - negative_last":
        return symbols_data["symbols_first"] - symbols_data["symbols_last"]
    elif formula == "positive_first_two - negative_last":
        return symbols_data["symbols_first_two"] - symbols_data["symbols_last"]
    return 0

def _calculate_error_count(symbols_data, error_method):
    """
    Calcule le nombre d'erreurs selon la méthode spécifiée.
    """
    if error_method == "negative_last":
        return symbols_data["symbols_last"]
    elif error_method == "negative_last_two":
        return symbols_data["symbols_last_two"]
    return 0

def _evaluate_metric_formula(formula, symbols_data):
    """
    Évalue une formule de métrique spéciale.
    """
    if "+" in formula:
        parts = formula.split(" + ")
        return sum(eval(part, {"__builtins__": {}}, symbols_data) for part in parts)
    return eval(formula, {"__builtins__": {}}, symbols_data)

