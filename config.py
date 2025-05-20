"""
Central configuration for the volleyball analysis application.
Contains complex mappings and configurations.
Simple constants have been moved to constants.py.
"""

from constants import MIN_ACTIONS, DEFAULT_THRESHOLDS, SET_MOMENTS, MAIN_TEAM

# Skill evaluation mappings
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

# Skill tabs mapping for UI
SKILL_TABS = {
    "Réception": {"skill": "Reception", "label": "réceptions"},
    "Block": {"skill": "Block", "label": "blocks"},
    "Service": {"skill": "Serve", "label": "service"},
    "Défense": {"skill": "Dig", "label": "défense"},
    "Attaque": {"skill": "Attack", "label": "attaque"},
    "Passe": {"skill": "Set", "label": "passes"}
}

# Display metrics configuration by skill
SKILL_DISPLAY_METRICS = {
    "Attack": ["% Efficacité", "% Kill", "% /", "% Erreur"],
    "Serve": ["% Efficacité", "% Ace", "% Positif", "% Frequence","% Erreur"],
    "Reception": ["% Efficacité", "% Parfaite", "% Erreur"],
    "Block": ["% Efficacité", "% Kill", "% Erreur"],
    "Dig": ["% Efficacité", "% Parfaite", "% Erreur"],
    "Set": ["% Efficacité", "% Jouable", "% Faute", "% FSO", "% SO"]
}

# Efficiency calculation formulas
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

# Error calculation formulas
ERROR_CALCULATION = {
    "Attack": "negative_last_two",  # (Faute + Contré) / Total
    "Serve": "negative_last",       # Faute / Total
    "Reception": "negative_last_two", # (Retour direct + Ace recu) / Total 
    "Block": "negative_last_two",     # (Faute + bloc out) / Total
    "Dig": "negative_last_two",      # (Renvoie direct + non défendu) / Total
    "Set": "negative_last"       # Faute / Total
}

# Special metrics by skill
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
        "% FSO" : "", # % of attack right after reception then pass that results in a point
        "% SO" : "" # % of points won when the team is in reception
    }
}

# Colors for each metric type (for visualization consistency)
METRIC_COLORS = {
    "% Kill": "green",
    "% Ace": "green",
    "% Parfaite": "green",
    "% Efficacité": "purple",
    "% Erreur": "red"
}

# Set types mapping
SET_TYPE = {
    "K1": "Fix Avant",
    "K2": "Fix Arrière",
    "K7": "Tendu",
    "KA": "CONTRE ATT SANS FIX",
    "KB": "Réception en 2 - Fix Arrière",
    "KC": "Basket",
    "KD": "Réception en 4 - Fix Arrière",
    "KE": "Pas de premier temps",
    "KF": "Réception en 4 - 5",
    "KI": "KI",
    "KJ": "KJ",
    "KK": "Réception en 2 - Fix en poste",
    "KL": "FLOTTANTE",
    "KM": "Réception en 2 - Fix Avant",
    "KN": "Mauvaise réception centrée",
    "KO": "Réception en 2 - 1",
    "KP": "Réception en 4 - Fix Avant",
    "KR": "CONTRE ATT AV FIX",
    "KS": "Réception en 4 - Tendue",
    "KT": "KT",
    "KX": "Réception en 2 - Tendue"
}

# Attack types mapping
ATTACK_TYPE = {
    'CB': 'Basket Deux Doigts',
    'CD': 'Basket Tête',
    'CF': 'Basket Mire',
    'P2': 'Attaque sur deuxième touche',
    'PK': 'Attaque non classifiable',
    'PP': 'Première main du passeur',
    'PR': 'Retour Direct',
    'V0': 'Haute en 5',
    'V3': 'Haute en 3',
    'V5': 'Haute en 4',
    'V6': 'Haute en 2',
    'V8': 'Haute en 1',
    'VP': 'Pipe Haute',
    'X0': 'Accélérée en 5',
    'X1': 'Fix Avant',
    'X2': 'Fix Arrière',
    'X3': 'Croix',
    'X4': 'Demi derrière',
    'X5': 'Accélérée en 4',
    'X6': 'Accélérée en 2',
    'X7': 'Tendue',
    'X8': 'Accélérée en 1',
    'X9': '4 Exterval',
    'XB': 'Pipe 6-1',
    'XC': 'Fix Avant C',
    'XD': 'Double C',
    'XF': 'Basket du Pointu',
    'XM': 'Fix en poste 3',
    'XO': 'Fix Arrière du Pointu',
    'XP': 'Pipe',
    'XR': 'Pipe 6-5',
    'XT': '4 Interval'
}