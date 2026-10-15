"""Tests d'intégration de l'API avec TestClient.

À compléter : au moins /sante, /auth/login (OK et KO), une route protégée sans jeton
(401), PUT /incidents/{id}/statut avec le rôle direction (403).
"""

from api.models import Incident


def test_sante(client):
    """GET /sante répond 200 avec {"statut": "ok"}."""
    reponse = client.get("/sante")
    assert reponse.status_code == 200
    assert reponse.json() == {"statut": "ok"}


def test_login_ok(client, jeton_exploitant):
    """Un login valide renvoie un jeton Bearer."""
    # la fixture a déjà fait le login ; on vérifie juste qu'on a un jeton
    assert jeton_exploitant["Authorization"].startswith("Bearer ")


def test_login_mauvais_mot_de_passe(client):
    """Un mauvais mot de passe donne 401 « Identifiants invalides »."""
    reponse = client.post("/auth/login", json={"username": "exploitant01", "password": "mauvais"})
    assert reponse.status_code == 401
    assert reponse.json() == {"detail": "Identifiants invalides"}


def test_login_utilisateur_inconnu(client):
    """Un utilisateur inconnu donne le même 401 qu'un mauvais mot de passe."""
    reponse = client.post("/auth/login", json={"username": "inconnu", "password": "mauvais"})
    assert reponse.status_code == 401
    assert reponse.json() == {"detail": "Identifiants invalides"}


def test_route_protegee_sans_jeton(client):
    """Une route protégée appelée sans jeton répond 401."""
    assert client.get("/stations").status_code == 401


def test_route_protegee_jeton_invalide(client):
    """Une route protégée appelée avec un jeton invalide répond 401."""
    reponse = client.get("/stations", headers={"Authorization": "Bearer jeton.invalide.xyz"})
    assert reponse.status_code == 401


def test_put_statut_direction_interdit(client, jeton_direction):
    """Le rôle direction ne peut pas modifier un statut d'incident (403)."""
    reponse = client.put("/incidents/I2026-0002/statut", json={"statut": "en_cours"}, headers=jeton_direction)
    assert reponse.status_code == 403
    assert reponse.json() == {"detail": "Acces reserve au role exploitant"}


def test_put_statut_exploitant(client, session, jeton_exploitant):
    """L'exploitant change un statut, puis une transition interdite donne 422 (RG7)."""
    try:
        reponse = client.put("/incidents/I2026-0002/statut", json={"statut": "en_cours"}, headers=jeton_exploitant)
        assert reponse.status_code == 200
        assert reponse.json()["statut"] == "en_cours"

        # deuxième fois : en_cours -> en_cours est interdit
        reponse = client.put("/incidents/I2026-0002/statut", json={"statut": "en_cours"}, headers=jeton_exploitant)
        assert reponse.status_code == 422
        assert reponse.json() == {"detail": "Transition de statut non autorisee"}
    finally:
        # on remet la base dans son état initial
        incident = session.get(Incident, "I2026-0002")
        incident.statut = "ouvert"
        incident.date_resolution = None
        session.commit()


def test_put_incident_introuvable(client, jeton_exploitant):
    """Modifier le statut d'un incident inexistant répond 404."""
    reponse = client.put("/incidents/I2026-9999/statut", json={"statut": "resolu"}, headers=jeton_exploitant)
    assert reponse.status_code == 404


def test_pagination_stations(client, jeton_direction):
    """La pagination des stations renvoie le bon total et la bonne taille de page."""
    reponse = client.get("/stations?taille_page=50&page=1", headers=jeton_direction).json()
    assert reponse["total"] == 120
    assert len(reponse["resultats"]) == 50
    assert reponse["resultats"][0]["station_id"] == "S001"

    reponse = client.get("/stations?taille_page=50&page=3", headers=jeton_direction).json()
    assert len(reponse["resultats"]) == 20


def test_pagination_hors_bornes(client, jeton_direction):
    """Une page 0 ou une taille de page > 100 est refusée (422)."""
    assert client.get("/stations?page=0", headers=jeton_direction).status_code == 422
    assert client.get("/stations?taille_page=101", headers=jeton_direction).status_code == 422


def test_filtre_commune(client, jeton_direction):
    """Le filtre par commune ne renvoie que les stations de Lille."""
    reponse = client.get("/stations?commune=Lille&taille_page=100", headers=jeton_direction).json()
    assert reponse["total"] == 46


def test_station_introuvable(client, jeton_direction):
    """Une station existante est renvoyée, une inconnue donne 404."""
    assert client.get("/stations/S001", headers=jeton_direction).json()["nom"] == "Lille - Gare"
    reponse = client.get("/stations/S999", headers=jeton_direction)
    assert reponse.status_code == 404
    assert reponse.json() == {"detail": "Station introuvable"}


def test_trajets_filtres(client, jeton_direction):
    """Les filtres de période et de station des trajets sont appliqués."""
    reponse = client.get("/trajets?date_debut=2026-08-25&date_fin=2026-08-25", headers=jeton_direction).json()
    assert reponse["total"] == 311
    reponse = client.get("/trajets?station=S001&taille_page=100", headers=jeton_direction).json()
    for trajet in reponse["resultats"]:
        assert "S001" in (trajet["station_depart"], trajet["station_arrivee"])


def test_incidents_filtre_statut(client, jeton_direction):
    """Le filtre par statut ne renvoie que des incidents ouverts."""
    reponse = client.get("/incidents?statut=ouvert&taille_page=100", headers=jeton_direction).json()
    for incident in reponse["resultats"]:
        assert incident["statut"] == "ouvert"


def test_indicateurs(client, jeton_direction):
    """Les indicateurs répondent et l'activité par jour concorde avec le nombre de trajets."""
    activite = client.get("/indicateurs/activite-par-jour?date_debut=2026-08-24&date_fin=2026-08-30", headers=jeton_direction).json()["donnees"]
    total = client.get("/trajets?date_debut=2026-08-24&date_fin=2026-08-30", headers=jeton_direction).json()["total"]
    assert sum(jour["nb_trajets"] for jour in activite) == total

    assert len(client.get("/indicateurs/stations-actives", headers=jeton_direction).json()["donnees"]) == 10
    assert client.get("/indicateurs/incidents-par-statut", headers=jeton_direction).status_code == 200
