"""
Menu utilities for CSV processing, deterministic validation,
data transformations, and menu grouping.
"""

import io
from typing import Dict, List, Tuple
import pandas as pd
from schemas import DishInput, DishItem, ValidationReport


REQUIRED_CSV_COLUMNS = ["name", "price", "ingredients"]
OPTIONAL_CSV_COLUMNS = ["category", "dietary"]


def generate_sample_csv_content() -> str:
    """Generate string content for the sample CSV template."""
    return """name,category,price,ingredients,dietary
Paneer Tikka,Starters,260,"Paneer (cottage cheese), hung curd (yogurt), bell peppers, onions, mustard oil, ginger-garlic paste, garam masala, kasuri methi","Vegetarian, Gluten-Free"
Chicken 65,Starters,290,"Boneless chicken, ginger-garlic paste, red chili paste, curry leaves, lemon juice, yogurt, black pepper, cornstarch",Non-Vegetarian
Masala Dosa,South Indian,140,"Fermented rice and urad dal batter, potatoes, onions, mustard seeds, green chilies, curry leaves, turmeric","Vegetarian, Vegan-friendly"
Butter Chicken,Mains,360,"Tender roasted chicken, tomatoes, cashew nuts, butter, cream, ginger, garlic, kasuri methi, aromatic spices",Non-Vegetarian
Dal Tadka,Mains,190,"Yellow toor dal, onions, tomatoes, cumin seeds, garlic, green chilies, ghee, turmeric, fresh coriander","Vegetarian, Gluten-Free"
Vegetable Biryani,Rice & Biryani,240,"Aged basmati rice, mixed seasonal vegetables, saffron, mint leaves, fried onions, whole garam masala, yogurt","Vegetarian, Gluten-Free"
Garlic Naan,Breads,60,"Refined wheat flour, minced garlic, butter, fresh coriander, yeast, milk",Vegetarian
Gulab Jamun,Desserts,110,"Khoya (reduced milk solids), paneer, sugar syrup, cardamom, rose water, pistachios",Vegetarian
Mango Lassi,Beverages,90,"Fresh mango pulp, chilled yogurt, milk, green cardamom powder, sugar","Vegetarian, Gluten-Free"
South Indian Filter Coffee,Beverages,50,"Freshly brewed chicory-coffee decoction, full cream milk, sugar","Vegetarian, Gluten-Free"
"""


def parse_and_validate_csv(file_or_content: io.BytesIO | str) -> ValidationReport:
    """
    Parse a CSV file or string, validating each row deterministically.
    Catches invalid prices, missing ingredients, missing dish names.
    Returns a ValidationReport with structured errors and valid dishes.
    """
    report = ValidationReport()
    
    try:
        if isinstance(file_or_content, str):
            df = pd.read_csv(io.StringIO(file_or_content), skip_blank_lines=True, index_col=False)
        else:
            # BytesIO or file-like object
            df = pd.read_csv(file_or_content, skip_blank_lines=True, index_col=False)
    except Exception as e:
        report.errors.append(f"Failed to read CSV file format: {str(e)}")
        return report

    # Normalize column names (strip whitespace and lower case)
    df.columns = [str(col).strip().lower() for col in df.columns]
    report.total_rows = len(df)

    # Check required columns
    missing_cols = [col for col in REQUIRED_CSV_COLUMNS if col not in df.columns]
    if missing_cols:
        report.errors.append(
            f"CSV is missing mandatory column(s): {', '.join(missing_cols)}. "
            f"Required columns are: {', '.join(REQUIRED_CSV_COLUMNS)}"
        )
        return report

    for row_idx, (_, row) in enumerate(df.iterrows()):
        row_num = row_idx + 2  # 1-indexed accounting for header row
        
        # Check if entire row is empty/NaN
        if row.isna().all():
            continue

        raw_name = row.get("name")
        raw_price = row.get("price")
        raw_ingredients = row.get("ingredients")
        raw_category = row.get("category") if "category" in df.columns else "Mains"
        raw_dietary = row.get("dietary") if "dietary" in df.columns else ""

        # Validate with Pydantic DishInput
        try:
            # Handle NaN values gracefully
            name_val = "" if pd.isna(raw_name) else str(raw_name).strip()
            price_val = None if pd.isna(raw_price) else raw_price
            ingredients_val = "" if pd.isna(raw_ingredients) else str(raw_ingredients).strip()
            category_val = "Mains" if pd.isna(raw_category) or not str(raw_category).strip() else str(raw_category).strip()
            dietary_val = "" if pd.isna(raw_dietary) else str(raw_dietary).strip()

            dish_input = DishInput(
                name=name_val,
                category=category_val,
                price=price_val,
                ingredients=ingredients_val,
                dietary=dietary_val,
            )

            # Convert to full DishItem
            dish_item = DishItem(
                id=dish_input.id,
                name=dish_input.name,
                category=dish_input.category,
                price=dish_input.price,
                ingredients=dish_input.ingredients,
                dietary=dish_input.dietary,
                description_en="",
                description_ta="",
                description_hi="",
            )
            report.valid_dishes.append(dish_item)

        except Exception as ve:
            report.errors.append(f"Row {row_num} ('{raw_name if not pd.isna(raw_name) else 'Unknown'}'): {str(ve)}")

    return report


def group_dishes_by_category(dishes: List[DishItem]) -> Dict[str, List[DishItem]]:
    """Group list of dishes into an ordered category dictionary."""
    categories: Dict[str, List[DishItem]] = {}
    for dish in dishes:
        cat = dish.category.strip() or "General"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(dish)
    return categories


def format_price(amount: float, symbol: str = "₹") -> str:
    """Format price nicely with currency symbol (e.g. ₹260 or ₹260.50)."""
    if amount == int(amount):
        return f"{symbol}{int(amount)}"
    return f"{symbol}{amount:.2f}"


def export_dishes_to_csv(dishes: List[DishItem]) -> str:
    """Export current list of dishes with generated descriptions to CSV."""
    records = []
    for d in dishes:
        records.append({
            "name": d.name,
            "category": d.category,
            "price": d.price,
            "ingredients": d.ingredients,
            "dietary": d.dietary,
            "description_en": d.description_en,
            "description_ta": d.description_ta,
            "description_hi": d.description_hi,
        })
    df = pd.DataFrame(records)
    return df.to_csv(index=False)
