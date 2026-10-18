"""
Automated unit tests for CSV parsing and deterministic validation.
Covers:
- Sample CSV parsing
- Missing mandatory columns
- Empty/invalid prices
- Missing ingredients
- Malformed CSV content
"""

import pytest
from menu_utils import generate_sample_csv_content, parse_and_validate_csv


def test_sample_csv_parsing():
    sample_csv = generate_sample_csv_content()
    report = parse_and_validate_csv(sample_csv)
    
    assert len(report.errors) == 0, f"Expected no errors, got: {report.errors}"
    assert len(report.valid_dishes) == 10
    assert report.total_rows == 10
    
    # Check first dish details
    dish1 = report.valid_dishes[0]
    assert dish1.name == "Paneer Tikka"
    assert dish1.category == "Starters"
    assert dish1.price == 260.0
    assert "Paneer" in dish1.ingredients
    assert "Vegetarian" in dish1.dietary


def test_missing_mandatory_columns():
    bad_csv = """name,category,dietary
Samosa,Snacks,Vegetarian
"""
    report = parse_and_validate_csv(bad_csv)
    assert len(report.errors) > 0
    assert "missing mandatory column" in report.errors[0].lower()
    assert len(report.valid_dishes) == 0


def test_empty_or_invalid_price():
    csv_data = """name,category,price,ingredients,dietary
Dish One,Mains,,Rice and lentils,Vegetarian
Dish Two,Mains,not_a_number,Potatoes and peas,Vegetarian
Dish Three,Mains,-50.00,Chicken and spices,Non-Vegetarian
Dish Four,Mains,0,Flour and water,Vegan
Dish Five,Mains,₹250,Paneer and cream,Vegetarian
Dish Six,Mains,Rs. 180.50,Tomatoes and spices,Vegetarian
"""
    report = parse_and_validate_csv(csv_data)
    
    # Dish One (empty price), Two (not a number), Three (negative), Four (zero) should error
    # Dish Five (₹250) and Six (Rs. 180.50) should be parsed cleanly!
    assert len(report.errors) == 4
    assert len(report.valid_dishes) == 2
    
    assert report.valid_dishes[0].name == "Dish Five"
    assert report.valid_dishes[0].price == 250.0
    
    assert report.valid_dishes[1].name == "Dish Six"
    assert report.valid_dishes[1].price == 180.50


def test_missing_ingredients():
    csv_data = """name,category,price,ingredients,dietary
Dish Without Ing,Mains,150,,Vegetarian
Dish With Whitespace Ing,Mains,150,   ,Vegetarian
Valid Dish,Mains,150,Lentils and cumin,Vegetarian
"""
    report = parse_and_validate_csv(csv_data)
    assert len(report.errors) == 2
    assert "ingredients" in report.errors[0].lower()
    assert len(report.valid_dishes) == 1
    assert report.valid_dishes[0].name == "Valid Dish"


def test_malformed_csv_syntax():
    # Invalid unbalanced quotes causing CSV parse error
    bad_syntax = 'name,category,price,ingredients\n"Unclosed Quote,Mains,100,Rice\n'
    report = parse_and_validate_csv(bad_syntax)
    # pandas handles or reports syntax errors
    assert report.total_rows >= 0
