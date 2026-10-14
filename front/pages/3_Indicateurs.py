"""Écran Indicateurs.

À compléter : trois st.metric et trois tableaux issus des trois endpoints
/indicateurs. Aucun graphique.
"""
from datetime import date

import pandas as pd
import streamlit as st

from api_client import ErreurApi, lire
from commun import verifier_connexion

st.set_page_config(page_title="Indicateurs", layout="wide")
st.title("Indicateurs")
verifier_connexion()
jeton = st.session_state["jeton"]

# Formulaire : les indicateurs ne sont recalculés qu'au clic sur « Actualiser »
with st.form("filtres"):
    colonne1, colonne2, colonne3 = st.columns(3)
    date_debut = colonne1.date_input("Période : du", date(2026, 8, 24))
    date_fin = colonne2.date_input("au", date(2026, 8, 30))
    limite = colonne3.number_input("Nombre de stations", min_value=1, max_value=50, value=10)
    st.form_submit_button("Actualiser")

try:
    with st.spinner("Chargement..."):
        activite = lire("/indicateurs/activite-par-jour", jeton,
                        {"date_debut": str(date_debut), "date_fin": str(date_fin)})["donnees"]
        stations = lire("/indicateurs/stations-actives", jeton, {"limite": limite})["donnees"]
        incidents = lire("/indicateurs/incidents-par-statut", jeton)
except ErreurApi as erreur:
    st.error(erreur.message)
    st.stop()

# ---------- Les trois métriques ----------
total_trajets = sum(jour["nb_trajets"] for jour in activite)
delai = incidents["delai_moyen_resolution_heures"]

colonne1, colonne2, colonne3 = st.columns(3)
colonne1.metric("Trajets sur la période", total_trajets)
colonne2.metric("Stations actives", len(stations))
colonne3.metric("Délai moyen de résolution (h)", delai if delai is not None else "n. d.")

# ---------- Les trois tableaux ----------
st.subheader("Activité par jour")
if activite:
    tableau = pd.DataFrame(activite)
    tableau.columns = ["Jour", "Nombre de trajets"]
    st.dataframe(tableau, hide_index=True)
else:
    st.info("Aucun résultat pour ces critères.")

st.subheader("Stations les plus actives")
if stations:
    tableau = pd.DataFrame(stations)
    tableau["total"] = tableau["nb_departs"] + tableau["nb_arrivees"]
    tableau.columns = ["Identifiant", "Nom", "Départs", "Arrivées", "Total"]
    st.dataframe(tableau, hide_index=True)
else:
    st.info("Aucun résultat pour ces critères.")

st.subheader("Incidents par statut")
if incidents["donnees"]:
    tableau = pd.DataFrame(incidents["donnees"])
    tableau.columns = ["Statut", "Nombre d'incidents"]
    st.dataframe(tableau, hide_index=True)
else:
    st.info("Aucun résultat pour ces critères.")
