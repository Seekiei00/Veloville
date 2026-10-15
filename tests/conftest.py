"""Fixtures pytest communes.

À compléter : client TestClient de l'API, jetons pour exploitant01 et direction01,
session de base de données de test. Aucun secret en dur : lire .env.
"""

import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient

from api.database import SessionLocal
from api.main import app

load_dotenv()
MOT_DE_PASSE = os.getenv("MOT_DE_PASSE_RECETTE")


@pytest.fixture
def client():
    """Client de test de l'API FastAPI, sans serveur uvicorn."""
    return TestClient(app)


@pytest.fixture
def session():
    """Session de base de données ouverte pour le test, fermée ensuite."""
    session = SessionLocal()
    yield session
    session.close()


def entete_connexion(client, username):
    """Se connecte avec le compte de recette et renvoie l'en-tête Authorization ; ignore le test sans mot de passe."""
    if not MOT_DE_PASSE:
        pytest.skip("MOT_DE_PASSE_RECETTE n'est pas défini dans le .env")
    reponse = client.post("/auth/login", json={"username": username, "password": MOT_DE_PASSE})
    return {"Authorization": "Bearer " + reponse.json()["access_token"]}


@pytest.fixture
def jeton_exploitant(client):
    """En-tête d'authentification du compte exploitant01."""
    return entete_connexion(client, "exploitant01")


@pytest.fixture
def jeton_direction(client):
    """En-tête d'authentification du compte direction01."""
    return entete_connexion(client, "direction01")
