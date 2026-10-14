"""Écran Incidents.

À compléter : tableau filtrable par statut ; pour le rôle exploitant, changement de
statut d'un incident via l'API.
"""

import math

import pandas as pd
import streamlit as st

from api_client import ErreurApi, changer_statut_incident, lire
from commun import verifier_connexion

st.set_page_config(page_title="Incidents", layout="wide")
st.title("Incidents")
verifier_connexion()
jeton = st.session_state["jeton"]

if "message" in st.session_state:
    st.success(st.session_state.pop("message"))

colonne1, colonne2, colonne3 = st.columns(3)
statut = colonne1.selectbox("Statut", ["Tous", "ouvert", "en_cours", "resolu"])
taille_page = colonne2.selectbox("Taille de page", [10, 20, 50], index=1)
page = colonne3.number_input("Page", min_value=1, step=1)

params = {"page": page, "taille_page": taille_page}
if statut != "Tous":
    params["statut"] = statut

try:
    with st.spinner("Chargement..."):
        reponse = lire("/incidents", jeton, params)
except ErreurApi as erreur:
    st.error(erreur.message)
    st.stop()

incidents = reponse["resultats"]
st.write(f"{reponse['total']} incidents au total")

if not incidents:
    st.info("Aucun résultat pour ces critères.")
else:
    tableau = pd.DataFrame(incidents).fillna("")
    tableau = tableau[["incident_id", "date_signalement", "cible", "velo_id", "station_id", "type_incident", "statut", "date_resolution", "technicien"]]
    tableau.columns = ["Identifiant", "Signalé le", "Cible", "Vélo", "Station", "Type", "Statut", "Résolu le", "Technicien"]
    st.dataframe(tableau, hide_index=True)

nb_pages = max(1, math.ceil(reponse["total"] / taille_page))
st.caption(f"Page {page} sur {nb_pages}")

# ---------- Changement de statut (rôle exploitant uniquement) ----------
st.subheader("Changer le statut d'un incident")

if st.session_state["role"] != "exploitant":
    st.info("La modification des incidents est réservée aux exploitants.")
elif incidents:
    with st.form("changement_statut"):
        incident_id = st.selectbox("Incident", [i["incident_id"] for i in incidents])
        nouveau_statut = st.selectbox("Nouveau statut", ["en_cours", "resolu"])
        appliquer = st.form_submit_button("Appliquer")

    if appliquer:
        try:
            changer_statut_incident(jeton, incident_id, nouveau_statut)
            # On garde le message en session puis on recharge la page pour mettre le tableau à jour
            st.session_state["message"] = f"Statut de l'incident {incident_id} mis à jour : {nouveau_statut}."
            st.rerun()
        except ErreurApi as erreur:
            if erreur.code == 403:
                st.error("Vous n'avez pas le droit de modifier un incident.")
            elif erreur.code == 404:
                st.error("Incident introuvable.")
            elif erreur.code == 422:
                st.error("Transition de statut non autorisée.")
            else:
                st.error(erreur.message)
