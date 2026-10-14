"""Requêtes de consultation et changement de statut d'un incident."""

from datetime import datetime, timedelta

from sqlalchemy import func, or_, select

from api.models import Incident, Station, Trajet

TRANSITIONS_AUTORISEES = [("ouvert", "en_cours"), ("ouvert", "resolu"), ("en_cours", "resolu")]


def paginer(session, requete, page, taille_page):
    """Renvoie l'enveloppe paginée {total, page, taille_page, resultats}."""
    total = session.scalar(select(func.count()).select_from(requete.subquery()))
    resultats = session.scalars(requete.offset((page - 1) * taille_page).limit(taille_page)).all()
    return {"total": total, "page": page, "taille_page": taille_page, "resultats": resultats}


def lister_stations(session, commune, page, taille_page):
    requete = select(Station).order_by(Station.station_id)
    if commune:
        requete = requete.where(Station.commune == commune)
    return paginer(session, requete, page, taille_page)


def lister_trajets(session, date_debut, date_fin, station, page, taille_page):
    requete = select(Trajet).order_by(Trajet.depart_horodatage)
    if date_debut:
        requete = requete.where(Trajet.depart_horodatage >= date_debut)
    if date_fin:
        # date_fin incluse : on prend tout ce qui est avant le lendemain minuit
        requete = requete.where(Trajet.depart_horodatage < date_fin + timedelta(days=1))
    if station:
        requete = requete.where(or_(Trajet.station_depart == station, Trajet.station_arrivee == station))
    return paginer(session, requete, page, taille_page)


def lister_incidents(session, statut, page, taille_page):
    requete = select(Incident).order_by(Incident.date_signalement.desc())
    if statut:
        requete = requete.where(Incident.statut == statut)
    return paginer(session, requete, page, taille_page)


def transition_autorisee(statut_actuel, nouveau_statut):
    """RG7 : seules trois transitions sont possibles ; un incident résolu n'évolue plus."""
    return (statut_actuel, nouveau_statut) in TRANSITIONS_AUTORISEES


def changer_statut(session, incident_id, nouveau_statut):
    """Change le statut d'un incident.

    Renvoie None si l'incident n'existe pas ; lève ValueError si la transition
    est interdite (RG7). Au passage à "resolu", renseigne la date de
    résolution si elle est vide (RG8).
    """
    incident = session.get(Incident, incident_id)
    if incident is None:
        return None
    if not transition_autorisee(incident.statut, nouveau_statut):
        raise ValueError("Transition de statut non autorisee")

    incident.statut = nouveau_statut
    if nouveau_statut == "resolu" and incident.date_resolution is None:
        incident.date_resolution = datetime.now().replace(microsecond=0)
    session.commit()
    return incident
