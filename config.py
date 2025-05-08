"""
Configuration centrale pour l'application d'analyse de volleyball.
Contient les constantes, mappings et paramètres partagés entre tous les modules.
Toute modification de ces valeurs affectera le comportement global de l'application.
"""

# Seuil minimum d'actions pour l'inclusion dans les statistiques
MIN_ACTIONS = 5

# Configuration des compétences et leurs évaluations
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
    "Set": {}
}

# Mapping des onglets de compétences pour l'interface utilisateur
SKILL_TABS = {
    "Réception": {"skill": "Reception", "label": "réceptions"},
    "Block": {"skill": "Block", "label": "blocks"},
    "Service": {"skill": "Serve", "label": "service"},
    "Défense": {"skill": "Dig", "label": "défense"},
    "Attaque": {"skill": "Attack", "label": "attaque"},
}

# Seuils par défaut pour les objectifs de performance par compétence
DEFAULT_THRESHOLDS = {
    "Reception": 40,
    "Block": 20,
    "Attack": 30,
    "Dig": 35,
    "Serve": 25
}

# Nom standard de l'équipe principale à suivre
MAIN_TEAM = "France Avenir"

# Options pour les moments dans le set
SET_MOMENTS = ["Tout", "Début", "Milieu", "Fin"]