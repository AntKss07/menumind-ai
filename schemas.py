"""
Data validation schemas for MenuMind AI using Pydantic v2.
Ensures deterministic validation, price preservation, and structured LLM output.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
import uuid


class RestaurantInfo(BaseModel):
    """Metadata for the restaurant profile."""
    name: str = Field(default="Saffron & Spice Kitchen", min_length=1, description="Restaurant business name")
    tagline: Optional[str] = Field(default="Authentic Flavors, Handcrafted with Love", description="Optional marketing tagline")
    currency_symbol: str = Field(default="₹", description="Currency symbol for pricing display")


class DishInput(BaseModel):
    """Raw or imported dish entry before or during menu compilation."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str = Field(..., min_length=1, description="Dish name as presented to customers")
    category: str = Field(default="Mains", min_length=1, description="Menu section / category")
    price: float = Field(..., gt=0, description="Strict positive numeric price. Preserved outside AI generation.")
    ingredients: str = Field(..., min_length=1, description="Owner-supplied ingredient facts (comma-separated or list)")
    dietary: str = Field(default="", description="Owner-supplied dietary metadata (e.g. Vegetarian, Non-Vegetarian, Gluten-Free)")

    @field_validator("name", mode="before")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not str(v).strip():
            raise ValueError("Dish name cannot be empty.")
        return str(v).strip()

    @field_validator("category", mode="before")
    @classmethod
    def validate_category(cls, v: str) -> str:
        s = str(v).strip() if v else "Mains"
        return s if s else "Mains"

    @field_validator("price", mode="before")
    @classmethod
    def validate_price(cls, v: object) -> float:
        if v is None:
            raise ValueError("Price is missing.")
        # Handle string prices like "₹250", "250.00", " 180 "
        s = str(v).replace("₹", "").replace("Rs.", "").replace("rs.", "").replace(",", "").strip()
        if not s:
            raise ValueError("Price cannot be empty.")
        try:
            val = float(s)
        except ValueError:
            raise ValueError(f"Invalid numeric price format: '{v}'")
        if val <= 0:
            raise ValueError("Price must be greater than zero.")
        return round(val, 2)

    @field_validator("ingredients", mode="before")
    @classmethod
    def validate_ingredients(cls, v: str) -> str:
        if not v or not str(v).strip():
            raise ValueError("Ingredients must be provided to avoid AI hallucination.")
        return str(v).strip()

    @field_validator("dietary", mode="before")
    @classmethod
    def validate_dietary(cls, v: Optional[str]) -> str:
        if v is None:
            return ""
        return str(v).strip()


class LLMSingleDescriptionOutput(BaseModel):
    """Schema enforced on Ollama structured JSON responses."""
    dish_name: str = Field(..., description="The exact dish name provided in the prompt")
    description: str = Field(..., min_length=5, description="Concise, appetizing description strictly adhering to facts")


class DishItem(BaseModel):
    """Complete active menu dish item including multilingual descriptions and user edit tracking."""
    id: str
    name: str
    category: str
    price: float
    ingredients: str
    dietary: str = ""
    description_en: str = ""
    description_ta: str = ""
    description_hi: str = ""
    is_user_edited: Dict[str, bool] = Field(default_factory=lambda: {"en": False, "ta": False, "hi": False})

    def get_description(self, lang: str) -> str:
        """Fetch description for a specific language code ('en', 'ta', 'hi')."""
        if lang == "ta":
            return self.description_ta or self.description_en
        elif lang == "hi":
            return self.description_hi or self.description_en
        return self.description_en

    def set_description(self, lang: str, text: str, user_edited: bool = False) -> None:
        """Set description and update edit tracking flag."""
        text = text.strip()
        if lang == "ta":
            self.description_ta = text
            if user_edited:
                self.is_user_edited["ta"] = True
        elif lang == "hi":
            self.description_hi = text
            if user_edited:
                self.is_user_edited["hi"] = True
        else:
            self.description_en = text
            if user_edited:
                self.is_user_edited["en"] = True


class ValidationReport(BaseModel):
    """Summary of validation errors and warnings when processing CSV or manual input."""
    valid_dishes: List[DishItem] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    total_rows: int = 0
