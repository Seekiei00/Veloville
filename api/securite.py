"""Authentification et autorisation.

À compléter : vérification d'un mot de passe contre son hachage bcrypt, création et
décodage du JWT (secret et algorithme lus dans l'environnement),
dépendances utilisateur_courant() et exiger_role("exploitant").
"""

import os
from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_EXPIRATION_MINUTES", "60"))

# auto_error=False : sans jeton, on renvoie nous-mêmes un 401 (et pas un 403)
bearer = HTTPBearer(auto_error=False)


def verifier_mot_de_passe(mot_de_passe, hachage):
    """Vrai si le mot de passe en clair correspond au hachage bcrypt stocké."""
    return bcrypt.checkpw(mot_de_passe.encode(), hachage.encode())


def creer_jeton(username, role):
    """Crée un JWT signé contenant l'utilisateur, son rôle et une date d'expiration."""
    expiration = datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    contenu = {"sub": username, "role": role, "exp": expiration}
    return jwt.encode(contenu, JWT_SECRET, algorithm=JWT_ALGORITHM)


def utilisateur_courant(credentials: HTTPAuthorizationCredentials = Depends(bearer)):
    """Renvoie {"username", "role"} ; 401 si le jeton est absent, invalide ou expiré."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Authentification requise")
    try:
        contenu = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Jeton invalide ou expire")
    return {"username": contenu["sub"], "role": contenu["role"]}


def exiger_exploitant(utilisateur=Depends(utilisateur_courant)):
    """403 si l'utilisateur connecté n'a pas le rôle exploitant."""
    if utilisateur["role"] != "exploitant":
        raise HTTPException(status_code=403, detail="Acces reserve au role exploitant")
    return utilisateur
