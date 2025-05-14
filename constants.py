"""
Constantes utilisées à travers l'application.
Ce fichier contient uniquement les valeurs constantes qui ne contiennent pas de logique.
"""

# Seuil minimum d'actions pour l'inclusion dans les statistiques
MIN_ACTIONS = 30
MIN_SET = 100

# Nom standard de l'équipe principale à suivre
MAIN_TEAM = "France Avenir"

# Options pour les moments dans le set
SET_MOMENTS = ["Tout", "0-10", "10-20", "20+"]

# Seuils par défaut pour les objectifs de performance par compétence
DEFAULT_THRESHOLDS = {
    "Reception": 40,
    "Block": 20,
    "Attack": 30,
    "Dig": 35,
    "Serve": 25
}