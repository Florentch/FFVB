"""
Constants used throughout the application.
"""

# Minimum threshold of actions for inclusion in statistics
MIN_ACTIONS = 30
MIN_SET = 100
MAIN_TEAM = "France Avenir"

# Options for moments in the set
SET_MOMENTS = ["Tout", "0-10", "10-20", "20+"]

# Default thresholds for performance objectives by skill
DEFAULT_THRESHOLDS = {
    "Reception": 40,
    "Block": 20,
    "Attack": 30,
    "Dig": 35,
    "Serve": 25,
    # Seuils d'erreur (à ne pas dépasser)
    "Reception_Error": 10,
    "Block_Error": 15,
    "Attack_Error": 20,
    "Dig_Error": 15,
    "Serve_Error": 12
}

SKILL_TRANSLATION = {
    "Attack": "Attaque", 
    "Block": "Bloc", 
    "Serve": "Service",
    "Reception": "Réception", 
    "Dig": "Défense", 
    "Set": "Passe"
}

KEY_METRICS = ["% Efficacité", "% Kill", "% Erreur", "Total"]

DEFAULT_FILTERS = {
    'min_actions': 5,
    'max_matches': 10
}