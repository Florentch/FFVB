import pandas as pd
import numpy as np

class Player:
    def __init__(self, id_, first_name, last_name, number, df, post=None, team=None):
        self.id = id_
        self.first_name = first_name
        self.last_name = last_name
        self.number = number
        self.post = post
        self.team = team
        self.df = df
        self.df_reception = df[df['skill'] == 'Reception']
        self.df_block = df[df['skill'] == 'Block']

    def get_action_df(self, skill, moment="Tout", match_filter=None):
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

        return df

    @staticmethod
    def _compute_reception_stats(df):
        total = len(df)
        evals = {
            '#': 'Parfaites',
            '/': 'Bonnes',
            '+': 'Bonnes',
            '!': 'Mauvaises',
            '-': 'Mauvaises',
            '=': 'Ratées'
        }
        stats = {'Total': total}
        for symbol, label in evals.items():
            count = len(df[df['evaluation_code'] == symbol])
            stats[label] = stats.get(label, 0) + count

        for label in ['Parfaites', 'Bonnes', 'Mauvaises', 'Ratées']:
            stats[f"% {label}"] = round((stats[label] / total) * 100, 1) if total else 0.0

        return stats

    @staticmethod
    def _compute_block_stats(df):
        total = len(df)
        evals = {
            '#': 'Points',
            '+': 'Bon',
            '!': 'Soutenu',
            '-': 'Mauvais',
            '/': 'Faute de filet',
            '=': 'Block out'
        }
        stats = {'Total': total}
        for symbol, label in evals.items():
            stats[label] = len(df[df['evaluation_code'] == symbol])

        for label in evals.values():
            stats[f"% {label}"] = round((stats[label] / total) * 100, 1) if total else 0.0

        return stats

    def get_skill_stats(self, skill, moment="Tout", match_filter=None):
        df = self.get_action_df(skill, moment, match_filter)
        total = len(df)

        if total == 0:
            sample = self._SKILL_STATS_FUNCTIONS[skill](df)
            return {key: 0 for key in sample.keys()}

        return self._SKILL_STATS_FUNCTIONS[skill](df)

    def get_skill_percentages(self, skill, moment="Tout", match_filter=None):
        stats = self.get_skill_stats(skill, moment, match_filter)
        percent_keys = [k for k in stats if k.startswith('%')]
        return {k: stats[k] for k in percent_keys}

    _SKILL_STATS_FUNCTIONS = {
        "Reception": _compute_reception_stats.__func__,
        "Block": _compute_block_stats.__func__,
    }
