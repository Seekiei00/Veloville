"""Client HTTP centralisé vers l'API VéloVille.

À compléter : lire API_URL et API_TIMEOUT_SECONDES, ajouter l'en-tête
Authorization: Bearer <jeton>, lever ErreurApi (message en français)
sur erreur réseau, délai dépassé ou code HTTP d'erreur.
"""

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

# 127.0.0.1 plutôt que localhost : sous Windows, localhost ajoutait ~2 s par appel
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_TIMEOUT_SECONDES = float(os.getenv("API_TIMEOUT_SECONDES", "5"))


class ErreurApi(Exception):
    """Erreur levée lorsque l'API est injoignable ou répond en erreur."""

    def __init__(self, message, code=None):
        super().__init__(message)
        self.message = message
        self.code = code  # code HTTP (None si l'API n'a pas répondu)


def appeler_api(methode, chemin, jeton=None, params=None, corps=None):
    entetes = {}
    if jeton:
        entetes["Authorization"] = f"Bearer {jeton}"

    try:
        reponse = httpx.request(methode, API_URL + chemin, headers=entetes, params=params,
                                json=corps, timeout=API_TIMEOUT_SECONDES)
    except httpx.TimeoutException:
        raise ErreurApi("L'API ne répond pas (délai dépassé).")
    except httpx.HTTPError:
        raise ErreurApi("L'API est injoignable. Vérifiez qu'elle est démarrée.")

    if reponse.status_code == 401:
        raise ErreurApi("Session expirée ou invalide. Veuillez vous reconnecter.", 401)
    if reponse.status_code == 403:
        raise ErreurApi("Vous n'avez pas le droit d'effectuer cette action.", 403)
    if reponse.status_code >= 400:
        raise ErreurApi(f"L'API a répondu une erreur (code {reponse.status_code}).", reponse.status_code)
    return reponse.json()


def connexion(username, password):
    return appeler_api("POST", "/auth/login", corps={"username": username, "password": password})


def lire(chemin, jeton, params=None):
    return appeler_api("GET", chemin, jeton, params=params)


def changer_statut_incident(jeton, incident_id, statut):
    return appeler_api("PUT", f"/incidents/{incident_id}/statut", jeton, corps={"statut": statut})
