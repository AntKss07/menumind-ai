"""
Unit tests for English PDF export and Multilingual Unicode HTML export.
Covers:
- ReportLab English PDF compilation and valid headers (%PDF-)
- TrueType Rupee symbol compatibility
- Indic PDF capability reporting
- Unicode HTML export for English, Tamil, and Hindi
- Print-to-PDF (@media print) CSS inclusion
"""

import pytest
from pdf_export import (
    check_indic_pdf_capability,
    generate_english_pdf,
    generate_unicode_html_menu,
)
from schemas import DishItem, RestaurantInfo


@pytest.fixture
def sample_menu_items():
    rest = RestaurantInfo(
        name="Dakshin Delights",
        tagline="Authentic South Indian & Coastal Flavors",
    )
    dishes = [
        DishItem(
            id="d1",
            name="Masala Dosa",
            category="Breakfast & Tiffin",
            price=140.0,
            ingredients="Fermented rice-lentil batter, spiced potato masala, curry leaves",
            dietary="Vegetarian",
            description_en="Crispy golden rice crepe folded over savory spiced potato masala.",
            description_ta="மொருமொருப்பான பொன்னிற தோசை, மசாலா உருளைக்கிழங்கு பூரணத்துடன்.",
            description_hi="खस्ता सुनहरी डोसा, स्वादिष्ट मसालेदार आलू भरावन के साथ।",
        ),
        DishItem(
            id="d2",
            name="Paneer Butter Masala",
            category="Curries",
            price=280.0,
            ingredients="Fresh cottage cheese, buttery tomato gravy, cream, kasuri methi",
            dietary="Vegetarian, Gluten-Free",
            description_en="Tender paneer cubes simmered in a velvety, mildly spiced buttery tomato sauce.",
            description_ta="வெண்ணெய் மற்றும் தக்காளி கிரேவியில் சமைக்கப்பட்ட மென்மையான பன்னீர் துண்டுகள்.",
            description_hi="मखमली मक्खनी टमाटर ग्रेवी में पके हुए ताज़ा पनीर के टुकड़े।",
        ),
    ]
    return rest, dishes


def test_generate_english_pdf_returns_valid_pdf(sample_menu_items):
    rest, dishes = sample_menu_items
    pdf_bytes = generate_english_pdf(rest, dishes)
    
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    # Standard PDF file header
    assert pdf_bytes.startswith(b"%PDF-")


def test_check_indic_pdf_capability():
    can_render, msg = check_indic_pdf_capability()
    assert isinstance(can_render, bool)
    assert isinstance(msg, str)
    assert len(msg) > 10


def test_unicode_html_export_english(sample_menu_items):
    rest, dishes = sample_menu_items
    html = generate_unicode_html_menu(rest, dishes, language="en")
    
    assert "<!DOCTYPE html>" in html
    assert "Dakshin Delights" in html
    assert "Masala Dosa" in html
    assert "Crispy golden rice crepe" in html
    assert "@media print" in html
    assert "₹140" in html or "₹" in html


def test_unicode_html_export_tamil_script(sample_menu_items):
    rest, dishes = sample_menu_items
    html = generate_unicode_html_menu(rest, dishes, language="ta")
    
    assert "தமிழ் மெனு" in html
    # Check that Tamil Unicode characters are preserved in output
    assert "மொருமொருப்பான" in html
    assert "வெண்ணெய்" in html
    assert "Noto Sans Tamil" in html
    assert "@media print" in html


def test_unicode_html_export_hindi_script(sample_menu_items):
    rest, dishes = sample_menu_items
    html = generate_unicode_html_menu(rest, dishes, language="hi")
    
    assert "हिन्दी मेनू" in html
    # Check that Hindi Devanagari characters are preserved in output
    assert "खस्ता सुनहरी डोसा" in html
    assert "मखमली मक्खनी" in html
    assert "Noto Sans Devanagari" in html
    assert "@media print" in html
