"""Routeur incidents.

À compléter : GET /incidents (filtre statut, pagination) et
PUT /incidents/{incident_id}/statut (rôle exploitant).
"""

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from api.database import get_db
from api.schemas import ChangementStatut, IncidentSchema, PageIncidents
from api.securite import exiger_exploitant, utilisateur_courant
from api.services import consultation

router = APIRouter(prefix="/incidents", tags=["incidents"], dependencies=[Depends(utilisateur_courant)])


@router.get("", response_model=PageIncidents)
def lister_incidents(
    statut: Literal["ouvert", "en_cours", "resolu"] | None = None,
    page: int = Query(1, ge=1),
    taille_page: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return consultation.lister_incidents(db, statut, page, taille_page)


@router.put("/{incident_id}/statut", response_model=IncidentSchema, dependencies=[Depends(exiger_exploitant)])
def modifier_statut(incident_id: str, corps: ChangementStatut, db: Session = Depends(get_db)):
    try:
        incident = consultation.changer_statut(db, incident_id, corps.statut)
    except ValueError:
        raise HTTPException(status_code=422, detail="Transition de statut non autorisee")
    if incident is None:
        raise HTTPException(status_code=404, detail="Incident introuvable")
    return incident
