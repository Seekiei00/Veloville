"""Fonctions communes aux pages : connexion obligatoire et barre latérale."""

import streamlit as st


def verifier_connexion():
    """Arrête la page si personne n'est connecté (aucun appel à l'API)."""
    if "jeton" not in st.session_state:
        st.warning("Veuillez vous connecter.")
        st.page_link("app.py", label="Aller à la page de connexion")
        st.stop()

    st.sidebar.write(f"Connecté : **{st.session_state['username']}**")
    st.sidebar.write(f"Rôle : **{st.session_state['role']}**")
    if st.sidebar.button("Se déconnecter"):
        st.session_state.clear()
        st.switch_page("app.py")
