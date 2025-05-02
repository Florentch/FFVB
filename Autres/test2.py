import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from datavolley import read_dv
from player import Player
from team import Team
import pandas as pd
import numpy as np

# Remplace 'chemin/vers/ton_fichier.dvw' par le chemin réel de ton fichier
dv_instance = read_dv.DataVolley('data/CNVB_Spain.dvw')

# Extraction des actions (plays)
df = dv_instance.get_plays()

# Affichage des 5 premières lignes
# print(df.head(5))
# print(df.iloc[12])
# print(df.columns)

# Filtrer les attaques avec un code d'évaluation '+'
successful_attacks = df[(df['skill'] == 'Attack') & (df['evaluation_code'] == '+')]

print(df['skill'].unique())

# print(successful_attacks[['player_name', 'team', 'set_number', 'code']].head())

# print(df[df['player_name'] == 'THEO MARTZLUFF'])

t = Team(list(), df[df['team'] == 'CNVB 24-25'])
# print(t.df)



# Ajouter le nom du passeur précédent pour chaque attaque
df['SIMON FROUARD'] = np.where(
    (df['skill'] == 'Attack') & (df['skill'].shift(1) == 'Set') & (df['team'] == df['team'].shift(1)),
    df['player_name'].shift(1),
    np.nan
)
# Afficher les premières attaques avec le nom du passeur
# print(df[df['skill'] == 'Attack'][['team', 'player_name']].head())

# Récupération des joueurs
players_df = dv_instance.get_players()

# Affichage des colonnes disponibles
# print(players_df.columns)
# print(len(players_df))
# print(players_df.loc[5, 'name'])

players = []
for _, row in players_df.iterrows():
    player = Player(
        id_ = row['player_id'],
        first_name = row['name'],
        last_name = row['lastname'],
        number = row['player_number'],
        team = row['team'],
        df = df[df['player_id'] == row['player_id']]
    )
    players.append(player)

# print([p.first_name for p in players if p.team == "CNVB 24-25"])

p = players[3]
print(p.df_serve)
# print(f"{p.first_name} {p.last_name} - #{p.number} ({p.team})")
# print(p.df[['skill', 'evaluation_code']])
# print(p.perfect())



# Affichage des joueurs (nom complet, avec équipe)
# print(players_df[,['team', 'player_number', 'player_name']])