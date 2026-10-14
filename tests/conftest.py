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
    return TestClient(app)


@pytest.fixture
def session():
    session = SessionLocal()
    yield session
    session.close()


def entete_connexion(client, username):
    if not MOT_DE_PASSE:
        pytest.skip("MOT_DE_PASSE_RECETTE n'est pas défini dans le .env")
    reponse = client.post("/auth/login", json={"username": username, "password": MOT_DE_PASSE})
    return {"Authorization": "Bearer " + reponse.json()["access_token"]}


@pytest.fixture
def jeton_exploitant(client):
    return entete_connexion(client, "exploitant01")


@pytest.fixture
def jeton_direction(client):
    return entete_connexion(client, "direction01")
