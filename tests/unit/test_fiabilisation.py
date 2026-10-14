"""Tests des règles de fiabilisation : un cas valide et un cas rejeté par règle.

Aucune base de données n'est nécessaire.
"""

from datetime import date, datetime

import pytest

from api.services.fiabilisation import (
    Rejet,
    cible_valide,
    dates_incident_valides,
    est_doublon,
    fiabiliser_incident,
    fiabiliser_station,
    fiabiliser_trajet,
    normaliser_date,
    normaliser_entier_positif,
    normaliser_horodatage,
    normaliser_station_id,
    normaliser_statut,
    normaliser_velo_id,
    station_existe,
    technicien_manquant,
    usager_ref_valide,
)

STATIONS = {"S001", "S002"}

TRAJET = {
    "trajet_id": "T480001", "velo_id": "V1167", "depart_horodatage": "2026-08-24 08:39:56",
    "station_depart": "S001", "station_arrivee": "S002", "duree_secondes": "215",
    "type_usager": "abonne", "usager_ref": "Ued311b7d",
}

INCIDENT = {
    "incident_id": "I2026-0003", "date_signalement": "2026-07-04 13:00", "cible": "velo",
    "velo_id": "V0447", "station_id": "", "type_incident": "eclairage HS", "statut": "resolu",
    "date_resolution": "2026-07-07 14:00", "technicien": "M. Vandenberghe",
}

STATION = {
    "station_id": "S001", "nom": "Lille - Gare", "commune": "Lille", "capacite": "15",
    "latitude": "50.59932", "longitude": "3.21953", "date_mise_en_service": "2023-08-07",
}


# ---------- Règles élémentaires ----------

def test_station_id():
    assert normaliser_station_id("s001") == "S001"
    assert normaliser_station_id("STATION1") is None


def test_velo_id():
    assert normaliser_velo_id("v1281") == "V1281"
    assert normaliser_velo_id("V12") is None


def test_entier_positif():
    assert normaliser_entier_positif("215") == 215
    assert normaliser_entier_positif("0") is None
    assert normaliser_entier_positif("-120") is None
    assert normaliser_entier_positif("abc") is None


def test_horodatage():
    assert normaliser_horodatage("2026-08-24 08:39:56") == datetime(2026, 8, 24, 8, 39, 56)
    assert normaliser_horodatage("24/08/2026 11:01") == datetime(2026, 8, 24, 11, 1)
    assert normaliser_horodatage("hier") is None


def test_date():
    assert normaliser_date("2023-08-07") == date(2023, 8, 7)
    assert normaliser_date("2023/08/07") is None


def test_statut():
    assert normaliser_statut("En cours") == "en_cours"
    assert normaliser_statut("RESOLU") == "resolu"
    assert normaliser_statut("ferme") is None


def test_station_existe():
    assert station_existe("S001", STATIONS)
    assert not station_existe("S999", STATIONS)


def test_usager_ref():
    assert usager_ref_valide("abonne", "Ued311b7d")
    assert usager_ref_valide("occasionnel", "")
    assert not usager_ref_valide("abonne", "")
    assert not usager_ref_valide("occasionnel", "Ued311b7d")


def test_cible():
    assert cible_valide("velo", "V0001", "")
    assert cible_valide("station", "", "S001")
    assert not cible_valide("velo", "V0001", "S001")
    assert not cible_valide("station", "", "")


def test_dates_incident():
    signalement = datetime(2026, 7, 4, 13, 0)
    assert dates_incident_valides("resolu", signalement, datetime(2026, 7, 7))
    assert dates_incident_valides("ouvert", signalement, None)
    assert not dates_incident_valides("resolu", signalement, datetime(2026, 7, 1))
    assert not dates_incident_valides("resolu", signalement, None)
    assert not dates_incident_valides("en_cours", signalement, datetime(2026, 7, 7))


def test_technicien_manquant():
    assert technicien_manquant("en_cours", "")
    assert not technicien_manquant("ouvert", "")
    assert not technicien_manquant("resolu", "K. Mercier")


def test_doublon():
    deja_vues = set()
    assert not est_doublon({"a": "1"}, deja_vues)
    assert est_doublon({"a": "1"}, deja_vues)


# ---------- Lignes complètes ----------

def test_station_valide():
    station, avertissements = fiabiliser_station(STATION)
    assert station["capacite"] == 15
    assert avertissements == []


def test_station_capacite_nulle_rejetee():
    with pytest.raises(Rejet):
        fiabiliser_station({**STATION, "capacite": "0"})


def test_trajet_valide():
    trajet, avertissements = fiabiliser_trajet(TRAJET, STATIONS)
    assert trajet["duree_secondes"] == 215
    assert avertissements == []


def test_trajet_normalise():
    ligne = {**TRAJET, "velo_id": "v1167", "depart_horodatage": "24/08/2026 08:39"}
    trajet, avertissements = fiabiliser_trajet(ligne, STATIONS)
    assert trajet["velo_id"] == "V1167"
    assert len(avertissements) == 2


def test_trajet_arrivee_vide_acceptee():
    trajet, _ = fiabiliser_trajet({**TRAJET, "station_arrivee": ""}, STATIONS)
    assert trajet["station_arrivee"] is None


def test_trajet_station_inconnue_rejetee():
    with pytest.raises(Rejet) as erreur:
        fiabiliser_trajet({**TRAJET, "station_arrivee": "S999"}, STATIONS)
    assert erreur.value.colonne == "station_arrivee"


def test_trajet_duree_negative_rejetee():
    with pytest.raises(Rejet) as erreur:
        fiabiliser_trajet({**TRAJET, "duree_secondes": "-120"}, STATIONS)
    assert erreur.value.colonne == "duree_secondes"


def test_incident_valide():
    incident, avertissements = fiabiliser_incident(INCIDENT, STATIONS)
    assert incident["statut"] == "resolu"
    assert avertissements == []


def test_incident_statut_normalise_et_technicien_signale():
    ligne = {**INCIDENT, "statut": "En cours", "date_resolution": "", "technicien": ""}
    incident, avertissements = fiabiliser_incident(ligne, STATIONS)
    assert incident["statut"] == "en_cours"
    assert [a[0] for a in avertissements] == ["statut", "technicien"]


def test_incident_resolution_avant_signalement_rejetee():
    with pytest.raises(Rejet) as erreur:
        fiabiliser_incident({**INCIDENT, "date_resolution": "2026-07-03 09:00"}, STATIONS)
    assert erreur.value.colonne == "date_resolution"


def test_incident_station_inconnue_rejetee():
    ligne = {**INCIDENT, "cible": "station", "velo_id": "", "station_id": "S999"}
    with pytest.raises(Rejet):
        fiabiliser_incident(ligne, STATIONS)
