"""Calcul des trois indicateurs (module métier testé).

À compléter : activite_par_jour(session, date_debut, date_fin),
stations_actives(session, limite) et incidents_par_statut(session).
Les routeurs ne font qu'appeler ces fonctions.
"""
"""Calcul des trois indicateurs, directement en SQL (agrégation dans la base)."""

from sqlalchemy import text


def activite_par_jour(session, date_debut=None, date_fin=None):
    """Indicateur 1 : nombre de trajets par jour, bornes incluses, jours croissants."""
    sql = "SELECT depart_horodatage::date AS jour, count(*) AS nb_trajets FROM trajet WHERE 1 = 1"
    if date_debut:
        sql += " AND depart_horodatage::date >= :debut"
    if date_fin:
        sql += " AND depart_horodatage::date <= :fin"
    sql += " GROUP BY jour ORDER BY jour"

    lignes = session.execute(text(sql), {"debut": date_debut, "fin": date_fin})
    return [{"jour": ligne.jour, "nb_trajets": ligne.nb_trajets} for ligne in lignes]


def stations_actives(session, limite=10):
    """Indicateur 2 : stations avec le plus de départs + arrivées.

    Une arrivée vide (NULL) n'est comptée pour aucune station (RG3).
    """
    sql = """
        SELECT * FROM (
            SELECT s.station_id, s.nom,
                (SELECT count(*) FROM trajet t WHERE t.station_depart = s.station_id) AS nb_departs,
                (SELECT count(*) FROM trajet t WHERE t.station_arrivee = s.station_id) AS nb_arrivees
            FROM station s
        ) AS mouvements
        ORDER BY nb_departs + nb_arrivees DESC, station_id
        LIMIT :limite
    """
    lignes = session.execute(text(sql), {"limite": limite})
    return [dict(ligne._mapping) for ligne in lignes]


def incidents_par_statut(session):
    """Indicateur 3 : nombre d'incidents par statut et délai moyen de résolution (heures)."""
    repartition = session.execute(text(
        "SELECT statut, count(*) AS nb_incidents FROM incident GROUP BY statut ORDER BY statut"
    ))
    delai = session.scalar(text("""
        SELECT round(avg(extract(epoch FROM date_resolution - date_signalement) / 3600), 1)
        FROM incident
        WHERE statut = 'resolu' AND date_resolution IS NOT NULL
    """))
    return {
        "donnees": [dict(ligne._mapping) for ligne in repartition],
        "delai_moyen_resolution_heures": float(delai) if delai is not None else None,
    }
