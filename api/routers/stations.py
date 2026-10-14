"""Routeur stations.

À compléter : GET /stations (filtre commune, pagination) et GET /stations/{station_id}.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Station
from api.schemas import PageStations, StationSchema
from api.securite import utilisateur_courant
from api.services import consultation

router = APIRouter(prefix="/stations", tags=["stations"], dependencies=[Depends(utilisateur_courant)])


@router.get("", response_model=PageStations)
def lister_stations(
    commune: str | None = None,
    page: int = Query(1, ge=1),
    taille_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return consultation.lister_stations(db, commune, page, taille_page)


@router.get("/{station_id}", response_model=StationSchema)
def lire_station(station_id: str, db: Session = Depends(get_db)):
    station = db.get(Station, station_id)
    if station is None:
        raise HTTPException(status_code=404, detail="Station introuvable")
    return station
