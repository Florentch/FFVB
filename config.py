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
        '/': 'Faute de filet',
        '=': 'Block out'
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
        '#': 'Parfaite',
        '+': 'Bonne',
        '!': 'Ok',
        '-': 'Mauvaise',
        '/': 'Nulle',
        '=': 'Faute'
    }
}

# Mapping des onglets de compétences pour l'interface utilisateur
SKILL_TABS = {
    "Réception": {"skill": "Reception", "label": "réceptions"},
    "Block": {"skill": "Block", "label": "blocks"},
    "Service": {"skill": "Serve", "label": "service"},
    "Défense": {"skill": "Dig", "label": "défense"},
    "Attaque": {"skill": "Attack", "label": "attaque"},
    "Passe": {"skill": "Set", "label": "passes"}
}

# Configuration des métriques à afficher par compétence
SKILL_DISPLAY_METRICS = {
    "Attack": ["% Efficacité", "% Kill", "% /", "% Erreur"],
    "Serve": ["% Efficacité", "% Ace", "% Positif", "% Frequence","% Erreur"],
    "Reception": ["% Efficacité", "% Parfaite", "% Erreur"],
    "Block": ["% Efficacité", "% Kill", "% Erreur"],
    "Dig": ["% Efficacité", "% Parfaite", "% Erreur"],
    "Set": ["% Efficacité", "% Jouable", "% Faute", "% FSO", "% SO"]
}

# Dictionnaire définissant comment calculer l'efficacité pour chaque compétence
EFFICIENCY_CALCULATION = {
    "Attack": {
        "formula": "positive_first - negative_last_two",
        "description": "(Point - (Faute + Contré)) / Total"
    },
    "Serve": {
        "formula": "positive_first_two - negative_last",
        "description": "(Ace + Bon) - (Faute) / Total"
    },
    "Reception": {
        "formula": "positive_first_two - negative_last_two",
        "description": "((Parfait + Positive) - (Retour direct + Ace recu)) / Total"
    },
    "Block": {
        "formula": "positive_first - negative_last_two",
        "description": "(Kill bloc - (Faute + bloc out)) / Total"
    },
    "Dig": {
        "formula": "positive_first_two - negative_last_two",
        "description": "((Parfait + Positive) - (Renvoie direct + non défendu)) / Total"
    },
    "Set": {
        "formula": "positive_first_two - negative_last",
        "description": "(Jouable - Faute) / Total"
    }
}

# Dictionnaire définissant comment calculer les erreurs pour chaque compétence
ERROR_CALCULATION = {
    "Attack": "negative_last_two",  # (Faute + Contré) / Total
    "Serve": "negative_last",       # Faute / Total
    "Reception": "negative_last_two", # (Retour direct + Ace recu) / Total 
    "Block": "negative_last_two",     # (Faute + bloc out) / Total
    "Dig": "negative_last_two",      # (Renvoie direct + non défendu) / Total
    "Set": "negative_last"       # Faute / Total
}

# Configuration des métriques spéciales par compétence
SPECIAL_METRICS = {
    "Attack": {
        "% Kill": "symbols_first",
        "% /": "symbols_specific['/']"
    },
    "Serve": {
        "% Ace": "symbols_first",
        "% Positif": "symbols_specific['#'] + symbols_specific['+'] + symbols_specific['/']",
        "% Frequence" : "symbols_specific['#'] + symbols_specific['+'] + symbols_specific['/'] + symbols_specific['!'] + symbols_specific['-']"
    },
    "Reception": {
        "% Parfaite": "symbols_first"
    },
    "Block": {
        "% Kill": "symbols_first"
    },
    "Dig": {
        "% Parfaite": "symbols_first"
    },
    "Set" : {
        "% Jouable": "symbols_specific['#'] + symbols_specific['+'] + symbols_specific['/'] + symbols_specific['!'] + symbols_specific['-']", 
        "% Faute" : "symbols_specific['=']",
        "% FSO" : "", # % D'attaque juste après la recep puis passe qui correspond à un point
        "% SO" : "" #  % De point gagné sur lorsque l'équipe est en reception
    }
}

# Couleurs pour chaque type de métrique (pour harmoniser les visualisations)
METRIC_COLORS = {
    "% Kill": "green",
    "% Ace": "green",
    "% Parfaite": "green",
    "% Efficacité": "purple",
    "% Erreur": "red"
}