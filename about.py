import streamlit as st
from streamlit_extras.let_it_rain import rain


def about_tab():
    """
    Affiche la page À propos avec les informations sur l'auteur et le projet
    """
    
    st.markdown("""
    <div style="background: linear-gradient(90deg, #1f4e79, #2980b9); 
                padding: 2rem; 
                border-radius: 10px; 
                margin-bottom: 2rem;
                color: white;">
        <h1 style="margin: 0; text-align: center;">
            🏐 À propos de cette application 🏐
        </h1>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.markdown("""
        ### Développeur
        **Florent CHEYRON**
        
        📧 **Contact :** florentcheyron@gmail.com
        
        💼 **Contexte :** Stage de Master 1 en Sciences du Numérique et Sport 
        
        📅 **Période :** 28 avril - 30 mai 2025
        """)
        
    with col2:
        st.markdown("""
        ### Projet
        **Analyse CNVB Saison 2024-2025**
        
        **Objectif :** Analyse statistique des performances en volleyball
        
        **Technologies :** Python, Streamlit
        
        **Fonctionnalités :** 
        - Statistiques globales d'équipe
        - Analyse détaillée par action
        - Évolution des performances joueurs
        - Comparaisons entre deux joueurs
        """)
    
    st.markdown("---")

    st.markdown("""
    ### Description du projet
    
    Cette application a été développée dans le cadre d'un stage pour analyser les performances 
    de l'équipe de volleyball du CNVB durant la saison 2024-2025. Elle permet aux entraîneurs 
    et analystes de :
    
    - **Visualiser les statistiques globales** des équipes de ligue B, et des joueurs de l'équipe France Avenir
    - **Analyser les actions techniques** (service, réception, attaque, défense, passe, bloc.)
    - **Suivre l'évolution** des performances individuelles des joueurs de France Avenir sur leur matchs de la saison
    - **Comparer les joueurs** entre eux sur différents critères et par rapport au meilleur en terme d'efficacité
    
    L'interface interactive facilite l'exploration des données et la prise de décision tactique.
    """)
    
    with st.expander("🔧 Informations techniques"):
        st.markdown("""
        **Stack technique :**
        - **Frontend :** Streamlit
        - **Traitement des données :** Pandas, NumPy
        - **Visualisations :** Plotly, Matplotlib
        - **Langage :** Python 3.10 + 
        
        **Fonctionnalités avancées :**
        - Filtrage dynamique par sets et moments de jeu
        - Graphiques interactifs et responsive
        - Export des données et visualisations
        - Interface utilisateur intuitive
        """)

    st.markdown("---")

    col1, col2 , _= st.columns(3)

    with col1:
        vb = st.toggle("Mode Volley Ball")
        if vb: volley_ball_mode()
        
    with col2:
        if st.checkbox("Afficher les statistiques de l'application"):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Lignes de code", "~3 000")
            
            with col2:
                st.metric("Modules Python", "15")
                
            with col3:
                st.metric("Version", "1.0.0")



    st.markdown("""
    <div style="text-align: center; 
                color: #666; 
                font-style: italic; 
                margin-top: 2rem;">
        Développé pour l'analyse sportive | Stage 2025
    </div>
    """, unsafe_allow_html=True)


def volley_ball_mode():
    rain(
        emoji="🏐",
        font_size=77,
        falling_speed=7,
        animation_length="infinite",
    )
    