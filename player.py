import pandas as pd
import numpy as np

class Player:
    SKILL_EVAL_MAPPINGS = {
            "Reception": {
                '#': 'Parfaite',
                '+': 'Positif',
                '!': 'Exclamative',
                '-': 'Négatif',
                '/': 'Retour direct',
                '=': 'Ace reçu'
            },
            "Block": {
                '#': 'Kill bloc',
                '+': 'Positif',
                '!': 'Soutenu',
                '-': 'Négatif',
                '/': 'Contré',
                '=': 'Fautes'
            },
            "Serve": {
                '#': 'Ace',
                '/': 'Bon',
                '+': 'Positif',
                '!': 'Exclamative',
                '-': 'Negatif',
                '=': 'Faute'
            },
            "Attack": {
                '#': 'Point',
                '+': 'Positif',
                '!': 'Soutenu',
                '-': 'Négatif',
                '/': 'Contré',
                '=': 'Faute'
            },
            "Dig": {
                '#': 'Parfaite',
                '+': 'Bonne',
                '!': 'Soutien de bloc',
                '-': 'Mauvaise',
                '/': 'Renvoi direct',
                '=': 'Non defendu'
            },
            "Set": {
            }
        }

    def __init__(self, id_, first_name, last_name, number, df, post=None, team=None):
        self.id = id_
        self.first_name = first_name
        self.last_name = last_name
        self.number = number
        self.post = post
        self.team = team
        self.df = df

    def get_action_df(self, skill, moment="Tout", match_filter=None, set_filter = None):
        df = self.df[self.df['skill'] == skill].copy()

        if match_filter:
            if not isinstance(match_filter, list):
                match_filter = [match_filter]
            df = df[df['match_id'].isin(match_filter)]

        if moment == "Début":
            df = df[(df['home_team_score'] <= 10) & (df['visiting_team_score'] <= 10)]
        elif moment == "Milieu":
            df = df[((df['home_team_score'] > 10) & (df['home_team_score'] < 20)) &
                    ((df['visiting_team_score'] > 10) & (df['visiting_team_score'] < 20))]
        elif moment == "Fin":
            df = df[(df['home_team_score'] >= 20) | (df['visiting_team_score'] >= 20)]

        if set_filter is not None:
            if isinstance(set_filter, (list, tuple, set)):
                df = df[df['set_number'].isin(set_filter)]
            else:
                df = df[df['set_number'] == set_filter]

        return df

    def get_skill_stats(self, skill, moment="Tout", match_filter=None, set_filter = None):
        df = self.get_action_df(skill, moment, match_filter, set_filter)
        total = len(df)

        mapping = self.SKILL_EVAL_MAPPINGS.get(skill)
        if mapping is None:
            raise ValueError(f"Aucune évaluation définie pour la compétence : {skill}")

        if total == 0:
            sample = self.compute_skill_stats(df, mapping)
            return {key: 0 for key in sample.keys()}

        return self.compute_skill_stats(df, mapping)

    def get_skill_percentages(self, skill, moment="Tout", match_filter=None, set_filter = None):
        stats = self.get_skill_stats(skill, moment, match_filter)
        return {k: v for k, v in stats.items() if k.startswith('%')}

    @staticmethod
    def compute_skill_stats(df, eval_mapping):
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

        return stats

    @classmethod
    def get_skill_labels(cls, with_percent=True):
        labels = {}
        for skill, symbol_map in Player.SKILL_EVAL_MAPPINGS.items():
            seen = set()
            ordered_vals = []
            for val in symbol_map.values():
                if val not in seen:
                    ordered_vals.append(val)
                    seen.add(val)
            labels[skill] = [f"% {v}" if with_percent else v for v in ordered_vals]
        return labels



   
