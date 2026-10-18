"""
Unit tests for Pydantic schemas, validation constraints, and price preservation.
"""

import pytest
from pydantic import ValidationError
from schemas import DishInput, DishItem, LLMSingleDescriptionOutput, RestaurantInfo


def test_dish_input_valid():
    dish = DishInput(
        name="Chole Bhature",
        category="North Indian",
        price="180",
        ingredients="Chickpeas, whole wheat flour, onions, tomatoes, ginger, spices",
        dietary="Vegetarian",
    )
    assert dish.name == "Chole Bhature"
    assert dish.price == 180.0
    assert dish.category == "North Indian"


def test_dish_input_price_formatting():
    # Tests that currency symbols, commas, and decimals are correctly normalized
    d1 = DishInput(name="Dosa", price="₹120.50", ingredients="Rice, urad dal")
    assert d1.price == 120.50

    d2 = DishInput(name="Biryani", price="Rs. 350", ingredients="Basmati rice, chicken")
    assert d2.price == 350.0

    d3 = DishInput(name="Thali", price=" 400.00 ", ingredients="Assorted curries")
    assert d3.price == 400.0


def test_dish_input_invalid_prices():
    with pytest.raises(ValidationError):
        DishInput(name="Dosa", price="0", ingredients="Rice")

    with pytest.raises(ValidationError):
        DishInput(name="Dosa", price="-100", ingredients="Rice")

    with pytest.raises(ValidationError):
        DishInput(name="Dosa", price="free", ingredients="Rice")


def test_dish_input_empty_name_or_ingredients():
    with pytest.raises(ValidationError):
        DishInput(name="  ", price=100, ingredients="Rice")

    with pytest.raises(ValidationError):
        DishInput(name="Biryani", price=100, ingredients="")


def test_dish_item_user_edit_persistence():
    dish = DishItem(
        id="d1",
        name="Paneer Tikka",
        category="Starters",
        price=260.0,
        ingredients="Paneer, spices",
    )
    
    # Initially not edited
    assert dish.is_user_edited["en"] is False
    assert dish.get_description("en") == ""

    # Simulated AI generation
    dish.set_description("en", "AI generated description.", user_edited=False)
    assert dish.is_user_edited["en"] is False
    assert dish.get_description("en") == "AI generated description."

    # Manual user edit
    dish.set_description("en", "Owner custom description with secret masala.", user_edited=True)
    assert dish.is_user_edited["en"] is True
    assert dish.get_description("en") == "Owner custom description with secret masala."

    # Verify other languages remain untouched
    assert dish.is_user_edited["ta"] is False
    assert dish.is_user_edited["hi"] is False


def test_price_preservation_outside_model():
    """Verify that numerical prices are never mutated by description generation models."""
    dish = DishItem(
        id="d2",
        name="Mutton Rogan Josh",
        category="Mains",
        price=450.0,
        ingredients="Mutton, Kashmiri chilies, yogurt, fennel, cardamom",
    )
    original_price = dish.price

    # Even if LLM output contains numbers or different claims, dish.price is protected
    llm_out = LLMSingleDescriptionOutput(
        dish_name="Mutton Rogan Josh",
        description="Slow-cooked tender mutton infused with aromatic Kashmiri spices and rich yogurt.",
    )
    dish.set_description("en", llm_out.description, user_edited=False)

    assert dish.price == original_price
    assert dish.price == 450.0
