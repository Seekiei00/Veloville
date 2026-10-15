"""Routeur auth.

À compléter : POST /auth/login.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from api.database import get_db
from api.models import Utilisateur
from api.schemas import LoginSchema
from api.securite import creer_jeton, verifier_mot_de_passe

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
def login(identifiants: LoginSchema, db: Session = Depends(get_db)):
    """Vérifie les identifiants et renvoie un JWT avec le rôle ; 401 si invalides."""
    utilisateur = db.scalar(select(Utilisateur).where(Utilisateur.username == identifiants.username))

    # Même message si l'identifiant est inconnu ou si le mot de passe est faux
    if utilisateur is None or not verifier_mot_de_passe(identifiants.password, utilisateur.mot_de_passe_hash):
        raise HTTPException(status_code=401, detail="Identifiants invalides")

    return {
        "access_token": creer_jeton(utilisateur.username, utilisateur.role),
        "token_type": "bearer",
        "role": utilisateur.role,
    }
