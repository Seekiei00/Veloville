"""Écran Stations.

À compléter : tableau des stations filtrable par commune, pagination.
"""

import math

import pandas as pd
import streamlit as st

from api_client import ErreurApi, lire
from commun import verifier_connexion

st.set_page_config(page_title="Stations", layout="wide")
st.title("Stations")
verifier_connexion()
jeton = st.session_state["jeton"]


@st.cache_data(ttl=3600)  # la liste des communes change rarement : on la garde 1 h
def charger_communes(_jeton):
    """Renvoie la liste triée des communes des stations (mise en cache 1 h)."""
    communes = set()
    for page in [1, 2]:  # 120 stations = 2 pages de 100
        reponse = lire("/stations", _jeton, {"page": page, "taille_page": 100})
        for station in reponse["resultats"]:
            communes.add(station["commune"])
    return sorted(communes)


try:
    communes = charger_communes(jeton)
except ErreurApi as erreur:
    st.error(erreur.message)
    st.stop()

colonne1, colonne2, colonne3 = st.columns(3)
commune = colonne1.selectbox("Commune", ["Toutes"] + communes)
taille_page = colonne2.selectbox("Taille de page", [10, 20, 50], index=1)
page = colonne3.number_input("Page", min_value=1, step=1)

params = {"page": page, "taille_page": taille_page}
if commune != "Toutes":
    params["commune"] = commune

try:
    with st.spinner("Chargement..."):
        reponse = lire("/stations", jeton, params)
except ErreurApi as erreur:
    st.error(erreur.message)
    st.stop()

st.write(f"{reponse['total']} stations au total")

if not reponse["resultats"]:
    st.info("Aucun résultat pour ces critères.")
else:
    tableau = pd.DataFrame(reponse["resultats"])
    tableau = tableau[["station_id", "nom", "commune", "capacite", "date_mise_en_service"]]
    tableau.columns = ["Identifiant", "Nom", "Commune", "Capacité", "Mise en service"]
    st.dataframe(tableau, hide_index=True)

nb_pages = max(1, math.ceil(reponse["total"] / taille_page))
st.caption(f"Page {page} sur {nb_pages}")
