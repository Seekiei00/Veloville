"""Import et fiabilisation des trois exports CSV dans PostgreSQL.

À compléter : lire data/stations.csv, data/trajets.csv et data/incidents.csv,
appliquer les règles de fiabilisation (api/services/fiabilisation.py),
charger les lignes valides, journaliser les rejets et les avertissements.
Le script doit être idempotent : deux exécutions successives laissent la
base dans le même état.

Usage prévu : python scripts/importer.py [--dossier data]
"""
import csv
import sys
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
sys.path.append(str(RACINE))

from sqlalchemy import delete, func, select  

from api.database import SessionLocal  
from api.models import Incident, Station, Trajet  
from api.services.fiabilisation import (  
    Rejet,
    est_doublon,
    fiabiliser_incident,
    fiabiliser_station,
    fiabiliser_trajet,
)

DOSSIER_DATA = RACINE / "data"
JOURNAL = RACINE / "docs" / "journal-import.csv"


def lire_csv(nom_fichier):
    with open(DOSSIER_DATA / nom_fichier, encoding="utf-8") as fichier:
        return list(csv.DictReader(fichier))


def traiter(nom_fichier, colonne_id, fiabiliser, journal):
    """Applique les règles à chaque ligne. Renvoie (lignes valides, compteurs)."""
    valides = []
    compteurs = {"lues": 0, "rejets": 0, "doublons": 0}
    deja_vues = set()

    for ligne in lire_csv(nom_fichier):
        compteurs["lues"] += 1
        identifiant = ligne[colonne_id]

        if est_doublon(ligne, deja_vues):
            compteurs["doublons"] += 1
            journal.append([nom_fichier, identifiant, "(ligne entière)", ",".join(ligne.values()), "ligne identique à une ligne déjà lue", "doublon écarté"])
            continue

        try:
            ligne_propre, avertissements = fiabiliser(ligne)
        except Rejet as rejet:
            compteurs["rejets"] += 1
            journal.append([nom_fichier, identifiant, rejet.colonne, rejet.valeur or "(vide)", rejet.motif, "rejet"])
            continue

        valides.append(ligne_propre)
        for colonne, valeur, motif in avertissements:
            decision = "avertissement" if colonne == "technicien" else "normalisation"
            journal.append([nom_fichier, identifiant, colonne, valeur or "(vide)", motif, decision])

    return valides, compteurs


def main():
    journal = []

    stations, bilan_stations = traiter("stations.csv", "station_id", fiabiliser_station, journal)
    ids_stations = {s["station_id"] for s in stations}
    trajets, bilan_trajets = traiter("trajets.csv", "trajet_id", lambda ligne: fiabiliser_trajet(ligne, ids_stations), journal)
    incidents, bilan_incidents = traiter("incidents.csv", "incident_id", lambda ligne: fiabiliser_incident(ligne, ids_stations), journal)

    # On vide puis on recharge : deux exécutions donnent le même résultat.
    with SessionLocal() as session:
        session.execute(delete(Trajet))
        session.execute(delete(Incident))
        session.execute(delete(Station))
        session.add_all([Station(**s) for s in stations])
        session.flush()  # les stations doivent exister avant les trajets et incidents
        session.add_all([Trajet(**t) for t in trajets])
        session.add_all([Incident(**i) for i in incidents])
        session.commit()

        print("Comptages en base :", "station =", session.scalar(select(func.count()).select_from(Station)), "| trajet =", session.scalar(select(func.count()).select_from(Trajet)), "| incident =", session.scalar(select(func.count()).select_from(Incident)))

    # utf-8-sig : le fichier s'ouvre correctement dans Excel
    with open(JOURNAL, "w", encoding="utf-8-sig", newline="") as fichier:
        ecrivain = csv.writer(fichier)
        ecrivain.writerow(["fichier", "identifiant", "colonne", "valeur", "motif", "decision"])
        ecrivain.writerows(journal)

    for nom, valides, bilan in [("stations.csv", stations, bilan_stations), ("trajets.csv", trajets, bilan_trajets), ("incidents.csv", incidents, bilan_incidents)]:
        print(f"{nom} : {bilan['lues']} lues = {len(valides)} importées + {bilan['rejets']} rejetées + {bilan['doublons']} doublons")
    print(f"Journal : docs/journal-import.csv ({len(journal)} lignes)")


if __name__ == "__main__":
    main()
