"""Routeur indicateurs.

À compléter : GET /indicateurs/activite-par-jour,
GET /indicateurs/stations-actives et
GET /indicateurs/incidents-par-statut.
"""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api.securite import utilisateur_courant
from api.services import indicateurs

router = APIRouter(prefix="/indicateurs", tags=["indicateurs"], dependencies=[Depends(utilisateur_courant)])


@router.get("/activite-par-jour")
def activite_par_jour(date_debut: date | None = None, date_fin: date | None = None, db: Session = Depends(get_db)):
    return {"donnees": indicateurs.activite_par_jour(db, date_debut, date_fin)}


@router.get("/stations-actives")
def stations_actives(limite: int = Query(10, ge=1, le=100), db: Session = Depends(get_db)):
    return {"donnees": indicateurs.stations_actives(db, limite)}


@router.get("/incidents-par-statut")
def incidents_par_statut(db: Session = Depends(get_db)):
    return indicateurs.incidents_par_statut(db)
