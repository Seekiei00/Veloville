"""Règles de fiabilisation des données (module métier testé).

À compléter : fonctions pures, sans accès à la base, qui normalisent ou rejettent
une valeur ou une ligne : horodatages, identifiants de vélo, statuts
d'incident, durées, références de station, cohérence des dates,
doublons. Chaque fonction retourne la valeur normalisée ou signale le
motif de rejet. Ces fonctions sont appelées par scripts/importer.py et
couvertes par tests/unit/.
"""

import re
from datetime import datetime

STATUTS = ["ouvert", "en_cours", "resolu"]


class Rejet(Exception):
    """Ligne rejetée : on garde la colonne, la valeur et le motif pour le journal."""

    def __init__(self, colonne, valeur, motif):
        """Mémorise la colonne fautive, la valeur lue et le motif du rejet."""
        super().__init__(motif)
        self.colonne = colonne
        self.valeur = valeur
        self.motif = motif


# ---------- Règles élémentaires ----------

def normaliser_station_id(valeur):
    """'s001' -> 'S001'. None si le format n'est pas S + 3 chiffres."""
    valeur = valeur.strip().upper()
    if re.fullmatch(r"S\d{3}", valeur):
        return valeur
    return None


def normaliser_velo_id(valeur):
    """'v1281' -> 'V1281'. None si le format n'est pas V + 4 chiffres."""
    valeur = valeur.strip().upper()
    if re.fullmatch(r"V\d{4}", valeur):
        return valeur
    return None


def normaliser_entier_positif(valeur):
    """Capacité (RG1) ou durée (RG4) : entier strictement positif, sinon None."""
    try:
        nombre = int(valeur)
    except ValueError:
        return None
    if nombre <= 0:
        return None
    return nombre


def normaliser_horodatage(valeur):
    """Accepte AAAA-MM-JJ HH:MM[:SS] et JJ/MM/AAAA HH:MM[:SS]. None si illisible."""
    for format_date in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"]:
        try:
            return datetime.strptime(valeur.strip(), format_date)
        except ValueError:
            pass
    return None


def normaliser_date(valeur):
    """Date AAAA-MM-JJ (ou JJ/MM/AAAA). None si illisible."""
    for format_date in ["%Y-%m-%d", "%d/%m/%Y"]:
        try:
            return datetime.strptime(valeur.strip(), format_date).date()
        except ValueError:
            pass
    return None


def normaliser_statut(valeur):
    """RG7 : 'En cours' -> 'en_cours', 'RESOLU' -> 'resolu'. None si inconnu."""
    valeur = valeur.strip().lower().replace(" ", "_")
    if valeur in STATUTS:
        return valeur
    return None


def station_existe(station_id, stations):
    """RG2 / RG6 : la station doit être dans le référentiel."""
    return station_id in stations


def usager_ref_valide(type_usager, usager_ref):
    """RG5 : un abonné a un pseudonyme U + 8 hexadécimaux, un occasionnel n'en a pas."""
    if type_usager == "occasionnel":
        return usager_ref == ""
    if type_usager == "abonne":
        return re.fullmatch(r"U[0-9a-f]{8}", usager_ref) is not None
    return False


def cible_valide(cible, velo_id, station_id):
    """RG6 : un incident vise soit un vélo, soit une station."""
    if cible == "velo":
        return velo_id != "" and station_id == ""
    if cible == "station":
        return station_id != "" and velo_id == ""
    return False


def dates_incident_valides(statut, date_signalement, date_resolution):
    """RG8 : date de résolution si et seulement si résolu, et après le signalement."""
    if statut == "resolu":
        return date_resolution is not None and date_resolution >= date_signalement
    return date_resolution is None


def technicien_manquant(statut, technicien):
    """RG8 : technicien attendu dès la prise en charge (simple avertissement)."""
    return statut in ["en_cours", "resolu"] and technicien.strip() == ""


def est_doublon(ligne, lignes_deja_vues):
    """Vrai si une ligne identique a déjà été lue. Sinon on la mémorise."""
    cle = tuple(ligne.values())
    if cle in lignes_deja_vues:
        return True
    lignes_deja_vues.add(cle)
    return False


# ---------- Fiabilisation d'une ligne complète ----------
# Chaque fonction renvoie (ligne_propre, avertissements) ou lève Rejet.
# Un avertissement est un tuple (colonne, valeur, motif).

def fiabiliser_station(ligne):
    """Valide une ligne de stations.csv (identifiant, capacité RG1, date) et la convertit."""
    station_id = normaliser_station_id(ligne["station_id"])
    if station_id is None:
        raise Rejet("station_id", ligne["station_id"], "identifiant de station invalide")
    capacite = normaliser_entier_positif(ligne["capacite"])
    if capacite is None:
        raise Rejet("capacite", ligne["capacite"], "capacité non entière ou <= 0")
    date_service = normaliser_date(ligne["date_mise_en_service"])
    if date_service is None:
        raise Rejet("date_mise_en_service", ligne["date_mise_en_service"], "date illisible")

    station = {
        "station_id": station_id,
        "nom": ligne["nom"].strip(),
        "commune": ligne["commune"].strip(),
        "capacite": capacite,
        "latitude": float(ligne["latitude"]),
        "longitude": float(ligne["longitude"]),
        "date_mise_en_service": date_service,
    }
    return station, []


def fiabiliser_trajet(ligne, stations):
    """Valide une ligne de trajets.csv (vélo, horodatage, stations, durée, usager) et la normalise."""
    avertissements = []

    velo_id = normaliser_velo_id(ligne["velo_id"])
    if velo_id is None:
        raise Rejet("velo_id", ligne["velo_id"], "identifiant de vélo invalide")
    if velo_id != ligne["velo_id"]:
        avertissements.append(("velo_id", ligne["velo_id"], "identifiant de vélo mis en majuscules"))

    depart = normaliser_horodatage(ligne["depart_horodatage"])
    if depart is None:
        raise Rejet("depart_horodatage", ligne["depart_horodatage"], "horodatage illisible")
    if "/" in ligne["depart_horodatage"]:
        avertissements.append(("depart_horodatage", ligne["depart_horodatage"], "date convertie au format AAAA-MM-JJ"))

    station_depart = normaliser_station_id(ligne["station_depart"])
    if station_depart is None or not station_existe(station_depart, stations):
        raise Rejet("station_depart", ligne["station_depart"], "station de départ inconnue")

    # RG3 : une arrivée vide est acceptée (vélo pas encore rendu)
    station_arrivee = None
    if ligne["station_arrivee"] != "":
        station_arrivee = normaliser_station_id(ligne["station_arrivee"])
        if station_arrivee is None or not station_existe(station_arrivee, stations):
            raise Rejet("station_arrivee", ligne["station_arrivee"], "station d'arrivée inconnue")

    duree = normaliser_entier_positif(ligne["duree_secondes"])
    if duree is None:
        raise Rejet("duree_secondes", ligne["duree_secondes"], "durée nulle ou négative")

    type_usager = ligne["type_usager"].strip().lower()
    if not usager_ref_valide(type_usager, ligne["usager_ref"]):
        raise Rejet("usager_ref", ligne["usager_ref"], "pseudonyme incohérent avec le type d'usager")

    trajet = {
        "trajet_id": ligne["trajet_id"].strip(),
        "velo_id": velo_id,
        "depart_horodatage": depart,
        "station_depart": station_depart,
        "station_arrivee": station_arrivee,
        "duree_secondes": duree,
        "type_usager": type_usager,
        "usager_ref": ligne["usager_ref"] or None,
    }
    return trajet, avertissements


def fiabiliser_incident(ligne, stations):
    """Valide une ligne d'incidents.csv (statut, cible, dates RG8, technicien) et la normalise."""
    avertissements = []

    statut = normaliser_statut(ligne["statut"])
    if statut is None:
        raise Rejet("statut", ligne["statut"], "statut inconnu")
    if statut != ligne["statut"]:
        avertissements.append(("statut", ligne["statut"], "statut normalisé"))

    cible = ligne["cible"].strip().lower()
    if not cible_valide(cible, ligne["velo_id"], ligne["station_id"]):
        raise Rejet("cible", ligne["cible"], "cible incohérente avec le vélo / la station")

    velo_id = None
    station_id = None
    if cible == "velo":
        velo_id = normaliser_velo_id(ligne["velo_id"])
        if velo_id is None:
            raise Rejet("velo_id", ligne["velo_id"], "identifiant de vélo invalide")
    else:
        station_id = normaliser_station_id(ligne["station_id"])
        if station_id is None or not station_existe(station_id, stations):
            raise Rejet("station_id", ligne["station_id"], "station inconnue")

    date_signalement = normaliser_horodatage(ligne["date_signalement"])
    if date_signalement is None:
        raise Rejet("date_signalement", ligne["date_signalement"], "date illisible")
    date_resolution = None
    if ligne["date_resolution"] != "":
        date_resolution = normaliser_horodatage(ligne["date_resolution"])
    if not dates_incident_valides(statut, date_signalement, date_resolution):
        raise Rejet("date_resolution", ligne["date_resolution"], "date de résolution incohérente")

    if technicien_manquant(statut, ligne["technicien"]):
        avertissements.append(("technicien", ligne["technicien"], "technicien absent alors que l'incident est pris en charge"))

    incident = {
        "incident_id": ligne["incident_id"].strip(),
        "date_signalement": date_signalement,
        "cible": cible,
        "velo_id": velo_id,
        "station_id": station_id,
        "type_incident": ligne["type_incident"].strip(),
        "statut": statut,
        "date_resolution": date_resolution,
        "technicien": ligne["technicien"].strip() or None,
    }
    return incident, avertissements
