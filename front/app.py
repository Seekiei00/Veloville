"""Page d'accueil Streamlit : connexion.

À compléter : formulaire identifiant / mot de passe, appel de POST /auth/login via
api_client, stockage du jeton et du rôle dans st.session_state,
message d'erreur en français en cas d'échec.

Lancement : streamlit run front/app.py
"""

import streamlit as st

from api_client import ErreurApi, connexion

st.set_page_config(page_title="VéloVille", layout="wide")
st.title("VéloVille — Plateforme de restitution")

# Déjà connecté : on affiche un message à la place du formulaire
if "jeton" in st.session_state:
    st.success(f"Connecté en tant que {st.session_state['username']} (rôle : {st.session_state['role']}).")
    st.write("Utilisez le menu latéral pour accéder aux écrans.")
    st.sidebar.write(f"Connecté : **{st.session_state['username']}**")
    st.sidebar.write(f"Rôle : **{st.session_state['role']}**")
    if st.button("Se déconnecter"):
        st.session_state.clear()
        st.rerun()
    st.stop()

st.header("Connexion")
with st.form("connexion"):
    username = st.text_input("Identifiant")
    password = st.text_input("Mot de passe", type="password")
    valider = st.form_submit_button("Se connecter")

if valider:
    try:
        reponse = connexion(username, password)
    except ErreurApi as erreur:
        if erreur.code in (401, 422):
            st.error("Identifiant ou mot de passe incorrect.")
        else:
            st.error(erreur.message)
    else:
        # Le jeton est gardé en session : jamais affiché, jamais dans l'URL
        st.session_state["jeton"] = reponse["access_token"]
        st.session_state["role"] = reponse["role"]
        st.session_state["username"] = username
        st.rerun()
