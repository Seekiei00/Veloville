"""Modèles ORM SQLAlchemy : Station, Trajet, Incident, Utilisateur.

À compléter : déclarer les quatre tables conformément à sql/schema.sql.
"""
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from api.database import Base


class Station(Base):
    __tablename__ = "station"

    station_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    nom: Mapped[str] = mapped_column(String(100))
    commune: Mapped[str] = mapped_column(String(50))
    capacite: Mapped[int] = mapped_column(Integer)
    latitude: Mapped[Decimal] = mapped_column(Numeric(8, 5))
    longitude: Mapped[Decimal] = mapped_column(Numeric(8, 5))
    date_mise_en_service: Mapped[date] = mapped_column(Date)


class Trajet(Base):
    __tablename__ = "trajet"

    trajet_id: Mapped[str] = mapped_column(String(12), primary_key=True)
    velo_id: Mapped[str] = mapped_column(String(8))
    depart_horodatage: Mapped[datetime] = mapped_column(DateTime)
    station_depart: Mapped[str] = mapped_column(ForeignKey("station.station_id"))
    station_arrivee: Mapped[str | None] = mapped_column(ForeignKey("station.station_id"))
    duree_secondes: Mapped[int] = mapped_column(Integer)
    type_usager: Mapped[str] = mapped_column(String(12))
    usager_ref: Mapped[str | None] = mapped_column(String(12))


class Incident(Base):
    __tablename__ = "incident"

    incident_id: Mapped[str] = mapped_column(String(12), primary_key=True)
    date_signalement: Mapped[datetime] = mapped_column(DateTime)
    cible: Mapped[str] = mapped_column(String(10))
    velo_id: Mapped[str | None] = mapped_column(String(8))
    station_id: Mapped[str | None] = mapped_column(ForeignKey("station.station_id"))
    type_incident: Mapped[str] = mapped_column(String(50))
    statut: Mapped[str] = mapped_column(String(10))
    date_resolution: Mapped[datetime | None] = mapped_column(DateTime)
    technicien: Mapped[str | None] = mapped_column(String(100))


class Utilisateur(Base):
    __tablename__ = "utilisateur"

    id_utilisateur: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    mot_de_passe_hash: Mapped[str] = mapped_column(String(100))
    role: Mapped[str] = mapped_column(String(20))
