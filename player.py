import pandas as pd
import numpy as np
from typing import List, Dict, Optional, Union

from config import EFFICIENCY_CALCULATION, ERROR_CALCULATION, SPECIAL_METRICS, SET_MOMENTS, SKILL_EVAL_MAPPINGS

class Player:
    """Player class representing a volleyball player with associated statistics."""

    def __init__(self, id_: str, first_name: str, last_name: str, number: str, df: pd.DataFrame, df_previous_actions: pd.DataFrame = None, df_next_actions: pd.DataFrame = None, post: str = None, team: str = None) -> None:
        self.id = id_
        self.first_name = first_name
        self.last_name = last_name
        self.number = number
        self.post = post
        self.team = team
        self.df = df
        self.df_previous_actions = df_previous_actions 
        self.df_next_actions = df_next_actions

    def get_action_df(self, skill: str, set_moment: str = "Tout", match_filter: Union[str, List[str]] = None, set_filter: Union[int, List[int]] = None) -> pd.DataFrame:
        """Filter player actions based on criteria."""
        df = self.df[self.df['skill'] == skill].copy()

        if match_filter:
            if not isinstance(match_filter, list):
                match_filter = [match_filter]
            df = df[df['match_id'].isin(match_filter)]

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

    def get_skill_stats(self, skill: str, set_moment: str = "Tout", match_filter: Union[str, List[str]] = None, set_filter: Union[int, List[int]] = None) -> Dict[str, Union[int, float]]:
        """Calculate statistics for a specific skill."""
        df = self.get_action_df(skill, set_moment, match_filter, set_filter)
        
        mapping = SKILL_EVAL_MAPPINGS.get(skill)
        if mapping is None:
            raise ValueError(f"No evaluation defined for skill: {skill}")

        if df.empty:
            sample = self.compute_skill_stats(df, mapping)
            return {key: 0 for key in sample.keys()}

        stats = self.compute_skill_stats(df, mapping)
        
        # Calculate specific metrics for sets
        if skill == "Set":
            fso_stats = self.calculate_set_fso(set_moment, match_filter, set_filter)
            so_stats = self.calculate_set_so(set_moment, match_filter, set_filter)
            stats["% FSO"] = fso_stats["% FSO"]
            stats["% SO"] = so_stats["% SO"]
        
        return stats

    def get_skill_percentages(self, skill: str, set_moment: str = "Tout", match_filter: Union[str, List[str]] = None, set_filter: Union[int, List[int]] = None) -> Dict[str, float]:
        """Extract only the percentages from skill statistics."""
        stats = self.get_skill_stats(skill, set_moment, match_filter, set_filter)
        return {k: v for k, v in stats.items() if k.startswith('%')}

    def get_skill_efficiency(self, skill: str, set_moment: str = "Tout", match_filter: Union[str, List[str]] = None, set_filter: Union[int, List[int]] = None) -> float:
        """Calculate efficiency for a specific skill."""
        df = self.get_action_df(skill, set_moment, match_filter, set_filter)
        if df.empty:
            return 0.0
            
        mapping = SKILL_EVAL_MAPPINGS.get(skill)
        if mapping is None or len(mapping) < 4:
            raise ValueError(f"Not enough evaluation symbols for skill: {skill}")
            
        symbols = list(mapping.keys())
        positive_symbols = symbols[:2]
        negative_symbols = symbols[-2:]
        
        positives = df[df['evaluation_code'].isin(positive_symbols)].shape[0]
        negatives = df[df['evaluation_code'].isin(negative_symbols)].shape[0]
        
        if negatives == 0:
            return 100.0 if positives > 0 else 0.0
        
        return round((positives / negatives) * 100, 1)

    @staticmethod
    def compute_skill_stats(df: pd.DataFrame, eval_mapping: Dict[str, str]) -> Dict[str, Union[int, float]]:
        """Calculate statistics from a DataFrame of actions and an evaluation mapping."""
        total = len(df)
        stats = {'Total': total}
        
        if total == 0:
            return {key: 0 for key in ['Total', '% Efficacité', '% Kill', '% Erreur', '% Parfaite', 
                                     '% Ace', '% Positif', '% /', '% Faute', '% Jouable']}
        
        skill = df['skill'].iloc[0] if not df.empty else None
        symbol_counts = df['evaluation_code'].value_counts()
        
        symbols = list(eval_mapping.keys())
        symbols_data = {
            "symbols_first": symbol_counts.get(symbols[0], 0) if symbols else 0,
            "symbols_first_two": sum(symbol_counts.get(symbol, 0) for symbol in symbols[:2]) if len(symbols) >= 2 else 0,
            "symbols_last": symbol_counts.get(symbols[-1], 0) if symbols else 0,
            "symbols_last_two": sum(symbol_counts.get(symbol, 0) for symbol in symbols[-2:]) if len(symbols) >= 2 else 0,
            "symbols_specific": {symbol: symbol_counts.get(symbol, 0) for symbol in symbols}
        }
        
        label_counts = {}
        for symbol, label in eval_mapping.items():
            count = symbol_counts.get(symbol, 0)
            label_counts[label] = label_counts.get(label, 0) + count
        
        stats.update(label_counts)
        
        for label, count in label_counts.items():
            stats[f"% {label}"] = round((count / total) * 100, 1) if total else 0.0
        
        if skill and skill in EFFICIENCY_CALCULATION:
            numerator = _calculate_efficiency_numerator(symbols_data, EFFICIENCY_CALCULATION[skill]["formula"])
            stats['% Efficacité'] = round((numerator / total) * 100, 1) if total else 0.0
        else:
            stats['% Efficacité'] = 0.0
        
        if skill and skill in ERROR_CALCULATION:
            error_count = _calculate_error_count(symbols_data, ERROR_CALCULATION[skill])
            stats['% Erreur'] = round((error_count / total) * 100, 1) if total else 0.0
            
            if skill == "Set":
                stats['% Faute'] = stats['% Erreur']
        else:
            stats['% Erreur'] = 0.0
        
        if skill and skill in SPECIAL_METRICS:
            for metric_name, metric_formula in SPECIAL_METRICS[skill].items():
                if not metric_formula:
                    stats[metric_name] = 0.0
                    continue
                    
                try:
                    result = _evaluate_metric_formula(metric_formula, symbols_data)
                    stats[metric_name] = round((result / total) * 100, 1) if total else 0.0
                except Exception:
                    stats[metric_name] = 0.0
        
        return stats

    @classmethod
    def get_skill_labels(cls, with_percent: bool = True) -> Dict[str, List[str]]:
        """Get all available evaluation labels for each skill."""
        labels = {}
        for skill, symbol_map in SKILL_EVAL_MAPPINGS.items():
            seen = set()
            ordered_vals = []
            for val in symbol_map.values():
                if val not in seen:
                    ordered_vals.append(val)
                    seen.add(val)
            skill_labels = [f"% {v}" if with_percent else v for v in ordered_vals]
            if with_percent and len(symbol_map) >= 4:
                skill_labels.append("% Efficacité")
            labels[skill] = skill_labels
        return labels

    def get_full_name(self) -> str:
        """Return player's full name."""
        return f"{self.first_name} {self.last_name}"

    def get_display_name(self) -> str:
        """Return player's display name with number."""
        return f"{self.number} – {self.last_name} {self.first_name}"

    def get_matches(self) -> List[str]:
        """Return list of match IDs the player participated in."""
        if self.df is None or self.df.empty:
            return []
        return self.df['match_id'].dropna().unique().tolist()

    def get_match_info(self, match_id: str) -> Optional[Dict[str, str]]:
        """Return basic information about a match."""
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

    def calculate_set_fso(self, set_moment: str = "Tout", match_filter: Union[str, List[str]] = None, set_filter: Union[int, List[int]] = None, set_type: str = "Tous", attack_type: str = "Tous") -> Dict[str, Union[int, float]]:
        """Calculate First Set Order (FSO) for a setter."""
        set_df = self._filter_set_df(set_moment, match_filter, set_filter, set_type)
        
        if set_df.empty or self.df_previous_actions is None or self.df_next_actions is None:
            return {"total_fso_situations": 0, "successful_fso": 0, "% FSO": 0.0}
        
        result_data = []
        for idx in set_df.index:
            if idx in self.df_previous_actions.index and idx in self.df_next_actions.index:
                prev_action = self.df_previous_actions.loc[idx]
                next_action = self.df_next_actions.loc[idx]
                
                if attack_type != "Tous" and not self._is_valid_attack(next_action, attack_type):
                    continue
                
                result_data.append({
                    'prev_skill': prev_action['skill'],
                    'next_skill': next_action['skill'],
                    'next_evaluation': next_action['evaluation_code']
                })
        
        if not result_data:
            return {"total_fso_situations": 0, "successful_fso": 0, "% FSO": 0.0}
        
        combined_df = pd.DataFrame(result_data)
        fso_situations = combined_df[
            (combined_df['prev_skill'] == 'Reception') & 
            (combined_df['next_skill'] == 'Attack')
        ]
        
        total_fso_situations = len(fso_situations)
        if total_fso_situations == 0:
            return {"total_fso_situations": 0, "successful_fso": 0, "% FSO": 0.0}
        
        successful_fso = fso_situations[fso_situations['next_evaluation'] == '#'].shape[0]
        fso_percentage = round((successful_fso / total_fso_situations) * 100, 1)
        
        return {
            "total_fso_situations": total_fso_situations,
            "successful_fso": successful_fso,
            "% FSO": fso_percentage
        }

    def calculate_set_so(self, set_moment: str = "Tout", match_filter: Union[str, List[str]] = None, set_filter: Union[int, List[int]] = None, set_type: str = "Tous", attack_type: str = "Tous") -> Dict[str, Union[int, float]]:
        """Calculate Set Order (SO) for a setter."""
        set_df = self._filter_set_df(set_moment, match_filter, set_filter, set_type)
        
        if set_df.empty or self.df_next_actions is None:
            return {"total_so_situations": 0, "successful_so": 0, "% SO": 0.0}
        
        result_data = []
        for idx in set_df.index:
            if idx in self.df_next_actions.index:
                next_action = self.df_next_actions.loc[idx]
                
                if attack_type != "Tous" and not self._is_valid_attack(next_action, attack_type):
                    continue
                
                result_data.append({
                    'next_skill': next_action['skill'],
                    'next_evaluation': next_action['evaluation_code']
                })
        
        if not result_data:
            return {"total_so_situations": 0, "successful_so": 0, "% SO": 0.0}
        
        combined_df = pd.DataFrame(result_data)
        so_situations = combined_df[combined_df['next_skill'] == 'Attack']
        
        total_so_situations = len(so_situations)
        if total_so_situations == 0:
            return {"total_so_situations": 0, "successful_so": 0, "% SO": 0.0}
        
        successful_so = so_situations[so_situations['next_evaluation'] == '#'].shape[0]
        so_percentage = round((successful_so / total_so_situations) * 100, 1)
        
        return {
            "total_so_situations": total_so_situations,
            "successful_so": successful_so,
            "% SO": so_percentage
        }

    def get_skill_stats_with_filters(self, skill: str, set_moment: str = "Tout", match_filter: Union[str, List[str]] = None, set_filter: Union[int, List[int]] = None, set_type: str = "Tous", attack_type: str = "Tous") -> Dict[str, Union[int, float]]:
        """Calculate statistics for a specific skill with additional filters."""
        if (set_type == "Tous" and attack_type == "Tous") and skill != "Set":
            return self.get_skill_stats(skill, set_moment, match_filter, set_filter)
        
        df = self.get_action_df(skill, set_moment, match_filter, set_filter)
        
        if set_type != "Tous" and 'set_code' in df.columns:
            df = df[df['set_code'] == set_type]
        
        if attack_type != "Tous" and skill == "Set" and self.df_next_actions is not None:
            valid_indices = []
            for idx in df.index:
                if idx in self.df_next_actions.index:
                    next_action = self.df_next_actions.loc[idx]
                    if self._is_valid_attack(next_action, attack_type):
                        valid_indices.append(idx)
            
            if valid_indices:
                df = df.loc[valid_indices]
            else:
                df = df.iloc[0:0]
        
        if df.empty:
            mapping = SKILL_EVAL_MAPPINGS.get(skill)
            if mapping is None:
                raise ValueError(f"No evaluation defined for skill: {skill}")
            
            sample = self.compute_skill_stats(df, mapping)
            return {key: 0 for key in sample.keys()}
        
        mapping = SKILL_EVAL_MAPPINGS.get(skill)
        if mapping is None:
            raise ValueError(f"No evaluation defined for skill: {skill}")
        
        stats = self.compute_skill_stats(df, mapping)
        
        if skill == "Set":
            fso_stats = self.calculate_set_fso(set_moment, match_filter, set_filter, set_type, attack_type)
            so_stats = self.calculate_set_so(set_moment, match_filter, set_filter, set_type, attack_type)
            stats["% FSO"] = fso_stats["% FSO"]
            stats["% SO"] = so_stats["% SO"]
        
        return stats
    
    def _filter_set_df(self, set_moment: str, match_filter: Union[str, List[str]], set_filter: Union[int, List[int]], set_type: str) -> pd.DataFrame:
        """Filter the set DataFrame according to given criteria."""
        set_df = self.get_action_df("Set", set_moment, match_filter, set_filter)
        
        if set_type != "Tous" and 'set_code' in set_df.columns:
            set_df = set_df[set_df['set_code'] == set_type]
            
        return set_df
    
    def _is_valid_attack(self, action: pd.Series, attack_type: str) -> bool:
        """Check if an action is an attack of the specified type."""
        return (action['skill'] == 'Attack' and 
                'attack_code' in action and 
                action['attack_code'] == attack_type)

    @classmethod
    def get_best_players_by_skill(cls, players: List['Player'], skill: str, set_moment: str = "Tout", match_filter: Union[str, List[str]] = None, set_filter: Union[int, List[int]] = None, min_actions: int = 10) -> Optional[Dict[str, Union['Player', float, int]]]:
        """Return the most efficient player for a given skill, with a minimum number of actions required."""
        valid_players = []
        
        for player in players:
            stats = player.get_skill_stats(skill, set_moment, match_filter, set_filter)
            
            if stats.get('Total', 0) >= min_actions:
                valid_players.append({
                    'player': player,
                    'efficiency': stats.get('% Efficacité', 0),
                    'total_actions': stats.get('Total', 0)
                })
        
        valid_players.sort(key=lambda x: x['efficiency'], reverse=True)
        
        if not valid_players:
            return None
            
        return valid_players[0]


def _calculate_efficiency_numerator(symbols_data: Dict[str, Union[int, Dict[str, int]]], formula: str) -> int:
    """Calculate the numerator for the efficiency formula."""
    if formula == "positive_first - negative_last_two":
        return symbols_data["symbols_first"] - symbols_data["symbols_last_two"]
    elif formula == "positive_first_two - negative_last_two":
        return symbols_data["symbols_first_two"] - symbols_data["symbols_last_two"]
    elif formula == "positive_first - negative_last":
        return symbols_data["symbols_first"] - symbols_data["symbols_last"]
    elif formula == "positive_first_two - negative_last":
        return symbols_data["symbols_first_two"] - symbols_data["symbols_last"]
    return 0

def _calculate_error_count(symbols_data: Dict[str, Union[int, Dict[str, int]]], error_method: str) -> int:
    """Calculate the number of errors according to the specified method."""
    if error_method == "negative_last":
        return symbols_data["symbols_last"]
    elif error_method == "negative_last_two":
        return symbols_data["symbols_last_two"]
    return 0

def _evaluate_metric_formula(formula: str, symbols_data: Dict[str, Union[int, Dict[str, int]]]) -> int:
    """Evaluate a special metric formula."""
    if "+" in formula:
        parts = formula.split(" + ")
        return sum(eval(part, {"__builtins__": {}}, symbols_data) for part in parts)
    return eval(formula, {"__builtins__": {}}, symbols_data)