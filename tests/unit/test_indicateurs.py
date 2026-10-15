"""Tests des fonctions de calcul des indicateurs.

À compléter : vérifier les agrégats sur un jeu de données connu.
"""
"""Tests des indicateurs sur le jeu de données fourni (base importée).

Les valeurs attendues ont été vérifiées à la main avec des requêtes SQL.
"""

from datetime import date

from api.services.consultation import transition_autorisee
from api.services.indicateurs import activite_par_jour, incidents_par_statut, stations_actives


def test_activite_par_jour(session):
    """Activité par jour sur une semaine : 7 jours et 2002 trajets au total."""
    resultat = activite_par_jour(session, date(2026, 8, 24), date(2026, 8, 30))
    assert len(resultat) == 7
    assert resultat[0] == {"jour": date(2026, 8, 24), "nb_trajets": 329}
    assert sum(jour["nb_trajets"] for jour in resultat) == 2002


def test_activite_un_seul_jour_bornes_incluses(session):
    """Une période d'un seul jour inclut ses deux bornes."""
    resultat = activite_par_jour(session, date(2026, 8, 25), date(2026, 8, 25))
    assert resultat == [{"jour": date(2026, 8, 25), "nb_trajets": 311}]


def test_activite_periode_vide(session):
    """Une période sans trajet renvoie une liste vide."""
    assert activite_par_jour(session, date(2026, 9, 1), date(2026, 9, 30)) == []


def test_activite_sans_parametre(session):
    """Sans période, toute l'activité est renvoyée."""
    assert len(activite_par_jour(session)) == 7


def test_stations_actives(session):
    """Les stations actives sont classées par nombre de passages décroissant."""
    resultat = stations_actives(session, 3)
    assert len(resultat) == 3
    assert resultat[0] == {"station_id": "S094", "nom": "Marcq-en-Baroeul - Grand Place", "nb_departs": 22, "nb_arrivees": 27}
    totaux = [s["nb_departs"] + s["nb_arrivees"] for s in resultat]
    assert totaux == sorted(totaux, reverse=True)


def test_incidents_par_statut(session):
    """Comptage des incidents par statut et délai moyen de résolution."""
    resultat = incidents_par_statut(session)
    assert sum(ligne["nb_incidents"] for ligne in resultat["donnees"]) == 177
    assert resultat["delai_moyen_resolution_heures"] == 129.4


def test_transitions_rg7():
    """Seules les transitions de statut autorisées par RG7 sont acceptées."""
    assert transition_autorisee("ouvert", "en_cours")
    assert transition_autorisee("ouvert", "resolu")
    assert transition_autorisee("en_cours", "resolu")
    assert not transition_autorisee("en_cours", "en_cours")
    assert not transition_autorisee("resolu", "ouvert")
