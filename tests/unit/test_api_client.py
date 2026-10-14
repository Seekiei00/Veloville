"""Tests du client HTTP du front (sans API démarrée)."""

import sys
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parents[2] / "front"))

import api_client 

def test_api_injoignable_message_en_francais(monkeypatch):
    monkeypatch.setattr(api_client, "API_URL", "http://127.0.0.1:9")  # port fermé
    with pytest.raises(api_client.ErreurApi) as erreur:
        api_client.lire("/stations", "jeton")
    assert erreur.value.message == "L'API est injoignable. Vérifiez qu'elle est démarrée."
