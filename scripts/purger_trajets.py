"""Supprime les trajets de plus de N jours (RGPD : 13 mois, soit 395 jours).

Par défaut on ne supprime rien (simulation) : il faut ajouter --appliquer.
Usage : python scripts/purger_trajets.py --jours 395 [--appliquer]
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  
from api.database import SessionLocal  

parser = argparse.ArgumentParser()
parser.add_argument("--jours", type=int, default=395)
parser.add_argument("--appliquer", action="store_true")
args = parser.parse_args()

date_limite = datetime.now() - timedelta(days=args.jours)

with SessionLocal() as session:
    nombre = session.scalar(text("SELECT count(*) FROM trajet WHERE depart_horodatage < :limite"), {"limite": date_limite})
    if args.appliquer:
        session.execute(text("DELETE FROM trajet WHERE depart_horodatage < :limite"), {"limite": date_limite})
        session.commit()
        print(f"{nombre} trajets antérieurs au {date_limite:%Y-%m-%d} supprimés.")
    else:
        print(f"Simulation : {nombre} trajets antérieurs au {date_limite:%Y-%m-%d} seraient supprimés "
            "(ajouter --appliquer pour supprimer).")
