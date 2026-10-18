"""
End-to-end integration and smoke tests for MenuMind AI workflow.
Distinguishes between mocked offline integration tests and live Ollama tests.
"""

import json
from unittest.mock import patch, MagicMock
import pytest
from ai_engine import OllamaClient
from menu_utils import export_dishes_to_csv, generate_sample_csv_content, parse_and_validate_csv
from pdf_export import generate_english_pdf, generate_unicode_html_menu
from schemas import RestaurantInfo


def test_full_offline_workflow_smoke():
    """Complete end-to-end simulation of user journey with mock generation."""
    # 1. Load sample CSV
    csv_text = generate_sample_csv_content()
    report = parse_and_validate_csv(csv_text)
    assert len(report.errors) == 0
    assert len(report.valid_dishes) == 10
    dishes = report.valid_dishes

    # 2. Simulate AI batch generation for English, Tamil, and Hindi
    mock_responses = {
        "en": "Delightful authentic dish prepared using genuine spices.",
        "ta": "பாரம்பரிய சுவையுடன் கூடிய சுவையான உணவுக் குறிப்பு.",
        "hi": "प्रामाणिक मसालों से तैयार स्वादिष्ट और लजीज व्यंजन।",
    }

    client = OllamaClient()
    for lang in ["en", "ta", "hi"]:
        with patch.object(client, "generate_description", return_value=(True, mock_responses[lang], None)):
            success_n, skipped_n, errors = client.batch_generate(
                dishes=dishes,
                language=lang,
                overwrite_user_edited=False,
            )
            assert success_n == 10
            assert len(errors) == 0

    # 3. Verify all dishes have descriptions in all 3 languages
    for d in dishes:
        assert d.get_description("en") == mock_responses["en"]
        assert d.get_description("ta") == mock_responses["ta"]
        assert d.get_description("hi") == mock_responses["hi"]
        assert d.price > 0

    # 4. Export to English PDF
    rest = RestaurantInfo(name="Spice Odyssey", tagline="Traditional Flavors")
    pdf_bytes = generate_english_pdf(rest, dishes)
    assert pdf_bytes.startswith(b"%PDF-")
    assert len(pdf_bytes) > 2000

    # 5. Export to Multilingual HTML
    for lang in ["en", "ta", "hi"]:
        html = generate_unicode_html_menu(rest, dishes, language=lang)
        assert "<!DOCTYPE html>" in html
        assert "Spice Odyssey" in html
        assert "@media print" in html

    # 6. Export updated CSV
    exported_csv = export_dishes_to_csv(dishes)
    assert "description_en" in exported_csv
    assert "description_ta" in exported_csv
    assert "description_hi" in exported_csv
    assert "Paneer Tikka" in exported_csv


def test_real_ollama_live_smoke():
    """
    Real environment smoke test.
    Checks actual Ollama daemon connectivity.
    If Ollama is not running, asserts that the health check fails gracefully
    and DOES NOT falsely report online status.
    """
    client = OllamaClient()
    is_online, msg, models = client.check_health()
    if is_online:
        print(f"\n[LIVE TEST] Real Ollama is ONLINE at {client.host}. Models: {models}")
        assert isinstance(models, list)
    else:
        print(f"\n[LIVE TEST] Real Ollama is OFFLINE: {msg}")
        assert is_online is False
        assert "Could not connect to Ollama" in msg or "HTTP status" in msg
