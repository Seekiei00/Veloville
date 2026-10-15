"""Schémas Pydantic (entrées et sorties de l'API).

À compléter : schémas de lecture des trois ressources, enveloppe paginée, corps de
connexion, réponse de connexion, corps de changement de statut, réponses
des trois indicateurs.
"""

# Schémas Pydantic : ce que l'API reçoit et renvoie.

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel


class StationSchema(BaseModel):
    """Station renvoyée par l'API, construite à partir du modèle ORM."""

    station_id: str
    nom: str
    commune: str
    capacite: int
    latitude: float
    longitude: float
    date_mise_en_service: date

    model_config = {"from_attributes": True}


class TrajetSchema(BaseModel):
    """Trajet renvoyé par l'API, construit à partir du modèle ORM."""

    trajet_id: str
    velo_id: str
    depart_horodatage: datetime
    station_depart: str
    station_arrivee: str | None
    duree_secondes: int
    type_usager: str
    usager_ref: str | None

    model_config = {"from_attributes": True}


class IncidentSchema(BaseModel):
    """Incident renvoyé par l'API, construit à partir du modèle ORM."""

    incident_id: str
    date_signalement: datetime
    cible: str
    velo_id: str | None
    station_id: str | None
    type_incident: str
    statut: str
    date_resolution: datetime | None
    technicien: str | None

    model_config = {"from_attributes": True}


# Enveloppes paginées
class PageStations(BaseModel):
    """Page de stations : total, numéro et taille de page, résultats."""

    total: int
    page: int
    taille_page: int
    resultats: list[StationSchema]


class PageTrajets(BaseModel):
    """Page de trajets : total, numéro et taille de page, résultats."""

    total: int
    page: int
    taille_page: int
    resultats: list[TrajetSchema]


class PageIncidents(BaseModel):
    """Page d'incidents : total, numéro et taille de page, résultats."""

    total: int
    page: int
    taille_page: int
    resultats: list[IncidentSchema]


# Authentification et modification d'un incident
class LoginSchema(BaseModel):
    """Corps de POST /auth/login : identifiant et mot de passe en clair."""

    username: str
    password: str


class ChangementStatut(BaseModel):
    """Corps de PUT /incidents/{id}/statut : nouveau statut parmi les trois valeurs de RG7."""

    statut: Literal["ouvert", "en_cours", "resolu"]