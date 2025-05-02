import pandas as pd
import numpy as np
from bokeh.plotting import figure, show
from bokeh.models import ColumnDataSource, Select, Tabs, DataTable, TableColumn, TabPanel
from bokeh.models import Slider, Div
from bokeh.layouts import column, row, layout
from bokeh.io import curdoc
from bokeh.palettes import Category10, Category20
from bokeh.transform import factor_cmap, dodge

# ==================== DÉFINITION DES FONCTIONS ====================

def create_global_view():
    """Crée la vue principale avec les statistiques globales"""
    # Graphique d'efficacité globale
    p1 = figure(title="Efficacité Globale", x_range=tous_joueurs, 
                height=400, width=800, toolbar_location="right")
    p1.vbar(x='nom', top='efficacite_globale', width=0.7, source=source_global,
           fill_color=color_mapper, line_color=color_mapper)
    p1.xaxis.major_label_orientation = 45
    p1.yaxis.axis_label = "Score d'efficacité (%)"
    p1.title.text_font_size = '14pt'
    
    # Tableau des statistiques clés
    columns = [
        TableColumn(field="nom", title="Nom"),
        TableColumn(field="equipe", title="Équipe"),
        TableColumn(field="service_acc", title="Prec. Service (%)"),
        TableColumn(field="service_ace", title="Aces"),
        TableColumn(field="attaque_pts", title="Pts Attaque"),
        TableColumn(field="attaque_acc", title="Prec. Attaque (%)"),
        TableColumn(field="recep_acc", title="Prec. Réception (%)"),
        TableColumn(field="efficacite_globale", title="Efficacité Globale")
    ]
    data_table = DataTable(source=source_global, columns=columns, width=800, height=300)
    
    return column(p1, data_table)

def create_comparison_view(skill_type):
    """Crée une vue de comparaison pour un type de compétence donné"""
    # Définition des catégories et titres selon le type de compétence
    if skill_type == 'service':
        categories = ['Précision (%)', 'Aces', 'Fautes', 'Total']
        value_fields = ['service_acc', 'service_ace', 'service_fault', 'service_total']
        title = "Comparaison des Services"
    elif skill_type == 'attaque':
        categories = ['Précision (%)', 'Points', 'Erreurs']
        value_fields = ['attaque_acc', 'attaque_pts', 'attaque_err']
        title = "Comparaison des Attaques"
    else:  # reception
        categories = ['Précision (%)', 'Réceptions Parfaites', 'Erreurs']
        value_fields = ['recep_acc', 'recep_parfaite', 'recep_err']
        title = "Comparaison des Réceptions"
    
    # Nombre maximum de joueurs à comparer
    max_joueurs = 6
    
    # Sélecteurs pour le nombre de joueurs à comparer
    nb_joueurs_div = Div(text="<strong>Nombre de joueurs à comparer:</strong>")
    nb_joueurs_slider = Slider(start=2, end=max_joueurs, value=2, step=1, title="")
    
    # Créer des sélecteurs pour les joueurs (jusqu'à max_joueurs)
    joueur_selects = []
    for i in range(max_joueurs):
        initial_value = tous_joueurs[i % len(tous_joueurs)]
        select = Select(title=f"Joueur {i+1}", options=tous_joueurs, value=initial_value)
        joueur_selects.append(select)
        # Cacher les sélecteurs au-delà du nombre initial
        if i >= 2:
            select.visible = False
            
    # Palette de couleurs pour les joueurs
    colors = Category10[10][:max_joueurs]  # Prendre les 6 premières couleurs
    
    # Préparer les données pour la visualisation groupée
    p = figure(title=title, x_range=categories, height=500, width=800,
               toolbar_location="right")
    
    # On va créer des sources de données pour chaque joueur
    sources_joueurs = [ColumnDataSource(data=dict(x=[], y=[], color=[])) for _ in range(max_joueurs)]
    
    # Calculer les décalages pour les positions des barres
    def get_offsets(n):
        total_width = 0.8  # Largeur totale du groupe
        bar_width = total_width / n
        offsets = [(i - (n-1)/2) * bar_width for i in range(n)]
        return offsets, bar_width
    
    # Barres pour les joueurs
    bar_renderers = []
    n_joueurs_actifs = 2  # Commencer avec 2 joueurs
    offsets, bar_width = get_offsets(n_joueurs_actifs)
    
    for i in range(max_joueurs):
        r = p.vbar(x=dodge('x', offsets[i % len(offsets)], range=p.x_range), top='y', 
                   width=bar_width, source=sources_joueurs[i],
                   color=colors[i], legend_label=f"Joueur {i+1}")
        bar_renderers.append(r)
        # Cacher les barres au-delà du nombre initial
        if i >= n_joueurs_actifs:
            r.visible = False
    
    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    p.legend.location = "top_right"
    p.xaxis.major_label_text_font_size = "12pt"
    
    # Mise à jour des données lors du changement de joueur sélectionné
    def update_data(attr, old, new):
        n_joueurs = int(nb_joueurs_slider.value)
        
        # Mettre à jour la visibilité des sélecteurs
        for i, select in enumerate(joueur_selects):
            select.visible = i < n_joueurs
        
        # Mettre à jour la visibilité des renderers de barres
        for i, renderer in enumerate(bar_renderers):
            renderer.visible = i < n_joueurs
            
        # Calculer les nouveaux décalages pour le nombre actuel de joueurs
        offsets, bar_width = get_offsets(n_joueurs)
        
        # Mettre à jour les données pour chaque joueur visible
        for i in range(n_joueurs):
            joueur_nom = joueur_selects[i].value
            joueur_data = []
            
            for field in value_fields:
                joueur_value = df[df['nom'] == joueur_nom][field].values[0]
                joueur_data.append(joueur_value)
                
            # Mise à jour de la source de données pour ce joueur
            sources_joueurs[i].data = {
                'x': categories,
                'y': joueur_data,
                'color': [colors[i]] * len(categories)
            }
            
            # Mettre à jour la position des barres
            bar_renderers[i].glyph.x = dodge('x', offsets[i], range=p.x_range)
            bar_renderers[i].glyph.width = bar_width
            
        # Mise à jour du titre
        players_str = " vs ".join([joueur_selects[i].value for i in range(n_joueurs)])
        p.title.text = f"{title}: {players_str}"
            
    # Mettre à jour les données au début
    update_data(None, None, None)
    
    # Ajouter les callbacks
    for select in joueur_selects:
        select.on_change('value', update_data)
    
    nb_joueurs_slider.on_change('value', update_data)
    
    # Organiser les contrôles
    selects_row1 = row(joueur_selects[0], joueur_selects[1], joueur_selects[2])
    selects_row2 = row(joueur_selects[3], joueur_selects[4], joueur_selects[5])
    slider_row = row(nb_joueurs_div, nb_joueurs_slider)
    
    controls = column(slider_row, selects_row1, selects_row2)
    return column(controls, p)

# ==================== PROGRAMME PRINCIPAL ====================

# Génération des données d'exemple
np.random.seed(42)

# Création des noms d'équipes et de joueurs
equipe_A = "Dragons"
equipe_B = "Phoenix"
joueurs_A = [f"Joueur A{i+1}" for i in range(6)]
joueurs_B = [f"Joueur B{i+1}" for i in range(6)]
tous_joueurs = joueurs_A + joueurs_B
equipes = [equipe_A] * 6 + [equipe_B] * 6

# Création des données statistiques
data = {
    'nom': tous_joueurs,
    'equipe': equipes,
    'service_acc': np.random.randint(30, 95, size=12),           # % de précision
    'service_ace': np.random.randint(0, 20, size=12),            # nombre d'aces
    'service_fault': np.random.randint(5, 30, size=12),          # nombre de fautes
    'attaque_pts': np.random.randint(20, 150, size=12),          # points marqués
    'attaque_acc': np.random.randint(30, 95, size=12),           # % de précision
    'attaque_err': np.random.randint(5, 40, size=12),            # erreurs
    'recep_parfaite': np.random.randint(10, 80, size=12),        # réceptions parfaites
    'recep_err': np.random.randint(5, 30, size=12),              # erreurs de réception
    'recep_tot': np.random.randint(50, 200, size=12),            # nombre total de réceptions
}

# Calcul des statistiques additionnelles
data['service_total'] = data['service_ace'] + data['service_fault'] + np.random.randint(30, 100, size=12)
data['recep_acc'] = np.round((data['recep_parfaite'] / data['recep_tot']) * 100, 1)  # % de précision en réception
data['efficacite_globale'] = np.round((data['service_acc'] + data['attaque_acc'] + data['recep_acc']) / 3, 1)

# Création du DataFrame
df = pd.DataFrame(data)

# Création de la source de données globale
source_global = ColumnDataSource(df)

# Couleurs par équipe
color_mapper = factor_cmap('equipe', palette=['#1E88E5', '#D81B60'], factors=[equipe_A, equipe_B])

# Création des différentes vues
global_view = create_global_view()
service_view = create_comparison_view('service')
attaque_view = create_comparison_view('attaque')
reception_view = create_comparison_view('recep')

# Organisation des vues en onglets
tab1 = TabPanel(child=global_view, title="Statistiques Globales")
tab2 = TabPanel(child=service_view, title="Comparaison Service")
tab3 = TabPanel(child=attaque_view, title="Comparaison Attaque")
tab4 = TabPanel(child=reception_view, title="Comparaison Réception")

tabs = Tabs(tabs=[tab1, tab2, tab3, tab4])

# Organisation de la mise en page finale
main_layout = column(
    row(column(
        tabs
    ))
)

# Ajout au document Bokeh
curdoc().add_root(main_layout)
curdoc().title = "Statistiques Volleyball"

# Pour exécuter l'application:
# bokeh serve --show nom_du_fichier.py
