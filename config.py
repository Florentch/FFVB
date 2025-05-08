"""
Configuration centrale pour l'application d'analyse de volleyball.
Contient les mappings et configurations plus complexes.
Les constantes simples ont été déplacées vers constants.py.
"""

from constants import MIN_ACTIONS, DEFAULT_THRESHOLDS, SET_MOMENTS, MAIN_TEAM

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