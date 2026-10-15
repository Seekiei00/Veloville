"""Tests des écrans du front Streamlit (avec AppTest, sans navigateur).

Les pages appellent l'API avec httpx : ici, on redirige ces appels vers
l'API FastAPI chargée en mémoire (TestClient). Pas besoin de lancer uvicorn.
La base doit être importée.
"""

import os
import sys
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient
from streamlit.testing.v1 import AppTest

from api.database import SessionLocal
from api.main import app
from api.models import Incident

DOSSIER_FRONT = Path(__file__).resolve().parents[2] / "front"
sys.path.append(str(DOSSIER_FRONT))  # pour que les pages trouvent api_client et commun

MOT_DE_PASSE = os.getenv("MOT_DE_PASSE_RECETTE")
client_api = TestClient(app)


@pytest.fixture(autouse=True)
def api_en_memoire(monkeypatch):
    """Envoie les appels httpx du front vers l'API en mémoire."""
    def fausse_requete(methode, url, headers=None, params=None, json=None, timeout=None):
        """Remplace httpx.request : transmet l'appel au TestClient en gardant le chemin."""
        chemin = "/" + url.split("/", 3)[3]  # "http://127.0.0.1:8000/stations" -> "/stations"
        return client_api.request(methode, chemin, headers=headers, params=params, json=json)

    monkeypatch.setattr(httpx, "request", fausse_requete)


def ouvrir_connexion():
    """Lance l'écran de connexion du front et renvoie l'AppTest."""
    return AppTest.from_file(str(DOSSIER_FRONT / "app.py"), default_timeout=30).run()


def se_connecter(username, mot_de_passe):
    """Remplit et valide le formulaire de connexion, puis renvoie l'écran obtenu."""
    ecran = ouvrir_connexion()
    ecran.text_input[0].input(username)
    ecran.text_input[1].input(mot_de_passe)
    ecran.button[0].click().run()
    return ecran


@pytest.fixture
def exploitant():
    """Écran du front connecté avec le compte exploitant01."""
    if not MOT_DE_PASSE:
        pytest.skip("MOT_DE_PASSE_RECETTE n'est pas défini dans le .env")
    return se_connecter("exploitant01", MOT_DE_PASSE)


@pytest.fixture
def direction():
    """Écran du front connecté avec le compte direction01."""
    if not MOT_DE_PASSE:
        pytest.skip("MOT_DE_PASSE_RECETTE n'est pas défini dans le .env")
    return se_connecter("direction01", MOT_DE_PASSE)


def textes(ecran, type_element):
    """Liste des messages affichés d'un type donné (success, info, warning, error)."""
    return [element.value for element in getattr(ecran, type_element)]


# ---------- Écran de connexion ----------

def test_connexion_ok(exploitant):
    """La connexion réussie affiche le rôle sans jamais afficher le jeton."""
    assert not exploitant.exception
    assert "Connecté en tant que exploitant01 (rôle : exploitant)." in textes(exploitant, "success")
    # le jeton est en session mais n'est jamais affiché
    jeton = exploitant.session_state["jeton"]
    tout_le_texte = " ".join(str(getattr(element, "value", "")) for element in exploitant.main)
    assert jeton not in tout_le_texte


def test_connexion_ko():
    """Une connexion échouée affiche une erreur et ne stocke pas de jeton."""
    ecran = se_connecter("exploitant01", "mauvais")
    assert textes(ecran, "error") == ["Identifiant ou mot de passe incorrect."]
    assert "jeton" not in ecran.session_state


def test_page_sans_connexion():
    """Une page ouverte sans connexion demande de se connecter et n'affiche rien."""
    ecran = ouvrir_connexion()
    ecran.switch_page("pages/1_Stations.py").run()
    assert textes(ecran, "warning") == ["Veuillez vous connecter."]
    assert len(ecran.dataframe) == 0


# ---------- Écran Stations ----------

def test_stations(exploitant):
    """L'écran Stations affiche un tableau de 20 lignes avec les bonnes colonnes."""
    exploitant.switch_page("pages/1_Stations.py").run()
    assert not exploitant.exception
    assert len(exploitant.dataframe) == 1
    assert len(exploitant.dataframe[0].value) == 20  # 20 stations par page
    assert list(exploitant.dataframe[0].value.columns) == ["Identifiant", "Nom", "Commune", "Capacité", "Mise en service"]


def test_stations_filtre_commune(exploitant):
    """Le filtre Commune de l'écran Stations ne montre que Lille."""
    exploitant.switch_page("pages/1_Stations.py").run()
    exploitant.selectbox[0].select("Lille").run()
    assert "46 stations au total" in [element.value for element in exploitant.markdown]
    assert set(exploitant.dataframe[0].value["Commune"]) == {"Lille"}


def test_stations_page_au_dela_de_la_derniere(exploitant):
    """Une page au-delà de la dernière affiche « Aucun résultat »."""
    exploitant.switch_page("pages/1_Stations.py").run()
    exploitant.number_input[0].set_value(99).run()
    assert textes(exploitant, "info") == ["Aucun résultat pour ces critères."]


# ---------- Écran Incidents ----------

def test_incidents_exploitant_change_un_statut(exploitant):
    """L'exploitant change le statut d'un incident depuis l'écran Incidents."""
    exploitant.switch_page("pages/2_Incidents.py").run()
    exploitant.selectbox[0].select("ouvert").run()
    incident_id = exploitant.selectbox[2].value  # liste « Incident » du formulaire
    try:
        exploitant.selectbox[3].select("en_cours")  # liste « Nouveau statut »
        bouton = [b for b in exploitant.button if b.label == "Appliquer"][0]
        bouton.click().run()
        assert f"Statut de l'incident {incident_id} mis à jour : en_cours." in textes(exploitant, "success")
    finally:
        # on remet l'incident dans son état initial
        with SessionLocal() as session:
            incident = session.get(Incident, incident_id)
            incident.statut = "ouvert"
            incident.date_resolution = None
            session.commit()


def test_incidents_direction_section_masquee(direction):
    """Le rôle direction voit les incidents sans le formulaire de modification."""
    direction.switch_page("pages/2_Incidents.py").run()
    assert not direction.exception
    assert len(direction.dataframe) == 1
    assert "La modification des incidents est réservée aux exploitants." in textes(direction, "info")
    assert "Appliquer" not in [b.label for b in direction.button]


# ---------- Écran Indicateurs ----------

def test_indicateurs(direction):
    """L'écran Indicateurs affiche les métriques et les trois tableaux attendus."""
    direction.switch_page("pages/3_Indicateurs.py").run()
    assert not direction.exception
    metriques = {m.label: m.value for m in direction.metric}
    assert metriques["Trajets sur la période"] == "2002"
    assert metriques["Stations actives"] == "10"
    assert "Délai moyen de résolution (h)" in metriques
    assert len(direction.dataframe) == 3  # activité, stations, incidents


# ---------- API arrêtée ----------

def test_api_arretee_message_en_francais(direction, monkeypatch):
    """API arrêtée : chaque écran affiche un message en français, sans trace Python."""
    def api_injoignable(*args, **kwargs):
        """Simule une API arrêtée en levant une erreur de connexion."""
        raise httpx.ConnectError("connexion refusée")

    monkeypatch.setattr(httpx, "request", api_injoignable)
    for page in ["pages/1_Stations.py", "pages/2_Incidents.py", "pages/3_Indicateurs.py"]:
        direction.switch_page(page).run()
        assert not direction.exception  # pas de trace Python
        assert textes(direction, "error") == ["L'API est injoignable. Vérifiez qu'elle est démarrée."]
