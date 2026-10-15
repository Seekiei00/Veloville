"""Tests du client HTTP du front (sans API démarrée)."""

import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[2] / "front"))

import api_client 

def test_api_injoignable_message_en_francais(monkeypatch):
    """Une API injoignable lève ErreurApi avec un message en français."""
    monkeypatch.setattr(api_client, "API_URL", "http://127.0.0.1:9")  # port fermé
    with pytest.raises(api_client.ErreurApi) as erreur:
        api_client.lire("/stations", "jeton")
    assert erreur.value.message == "L'API est injoignable. Vérifiez qu'elle est démarrée."


def test_ano_001_api_url_en_ipv4():
    """Non-régression ANO-001 : localhost ajoutait ~2 s par appel sous Windows."""
    contenu = (Path(__file__).resolve().parents[2] / ".env.example").read_text(encoding="utf-8")
    assert "API_URL=http://127.0.0.1:8000" in contenu
