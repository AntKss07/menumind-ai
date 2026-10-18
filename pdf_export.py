"""
Export functionality for MenuMind AI.
Includes:
- Robust English PDF generation via ReportLab with TrueType Indian Rupee (₹) symbol support.
- Indic script verification (WeasyPrint / HarfBuzz / Pango check).
- High-fidelity Unicode HTML Menu Studio export for English, Tamil, and Hindi
  with print-ready CSS for 1-click native PDF generation in browser.
"""

import io
import os
from typing import Dict, List, Optional, Tuple

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import HRFlowable, KeepTogether, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from menu_utils import format_price, group_dishes_by_category
from schemas import DishItem, RestaurantInfo


# Register Windows / system TrueType font for native Indian Rupee symbol (₹) support
FONT_NAME = "Helvetica"
HAS_RUPEE_FONT = False

for candidate in ["C:/Windows/Fonts/segoeui.ttf", "C:/Windows/Fonts/arial.ttf", "C:/Windows/Fonts/calibri.ttf"]:
    if os.path.exists(candidate):
        try:
            pdfmetrics.registerFont(TTFont("AppSegoe", candidate))
            bold_candidate = candidate.replace(".ttf", "bd.ttf")
            if os.path.exists(bold_candidate):
                pdfmetrics.registerFont(TTFont("AppSegoe-Bold", bold_candidate))
            else:
                pdfmetrics.registerFont(TTFont("AppSegoe-Bold", candidate))
            FONT_NAME = "AppSegoe"
            HAS_RUPEE_FONT = True
            break
        except Exception:
            continue


def check_indic_pdf_capability() -> Tuple[bool, str]:
    """
    Check if a system renderer capable of complex Indic glyph shaping
    (e.g., WeasyPrint with functional Pango / HarfBuzz) is available.
    """
    try:
        import weasyprint
        # Try a quick dummy render to verify cairo/pango DLLs are functional
        weasyprint.HTML(string="<p>Test</p>").write_pdf()
        return True, "Indic-capable PDF engine (WeasyPrint / Pango) is verified and available."
    except Exception as e:
        return (
            False,
            f"Indic PDF shaping engine not detected ({type(e).__name__}). "
            "ReportLab does not support complex Indic ligatures/matra shaping. "
            "MenuMind AI provides a high-fidelity Unicode HTML Export with @media print CSS "
            "for 100% authentic Tamil and Hindi glyph rendering via browser 'Save as PDF'."
        )


def generate_english_pdf(restaurant: RestaurantInfo, dishes: List[DishItem]) -> bytes:
    """
    Generate a clean, high-contrast, professional English PDF menu using ReportLab.
    Preserves exact dish names, numeric prices, and ingredient facts.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=36,
        rightMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()

    # Custom typography
    base_font = FONT_NAME if HAS_RUPEE_FONT else "Helvetica"
    bold_font = f"{FONT_NAME}-Bold" if HAS_RUPEE_FONT else "Helvetica-Bold"
    currency_prefix = "₹" if HAS_RUPEE_FONT else "Rs. "

    title_style = ParagraphStyle(
        "MenuTitle",
        fontName=bold_font,
        fontSize=24,
        leading=28,
        alignment=1,  # Center
        textColor=colors.HexColor("#1A202C"),
        spaceAfter=4,
    )

    tagline_style = ParagraphStyle(
        "MenuTagline",
        fontName=base_font,
        fontSize=10,
        leading=14,
        alignment=1,
        textColor=colors.HexColor("#718096"),
        spaceAfter=12,
    )

    category_style = ParagraphStyle(
        "MenuCategory",
        fontName=bold_font,
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#B7791F"),  # Warm amber/saffron
        spaceBefore=10,
        spaceAfter=4,
    )

    dish_name_style = ParagraphStyle(
        "DishName",
        fontName=bold_font,
        fontSize=10.5,
        leading=13,
        textColor=colors.HexColor("#2D3748"),
    )

    dietary_style = ParagraphStyle(
        "DishDiet",
        fontName=base_font,
        fontSize=7.5,
        leading=9,
        textColor=colors.HexColor("#38A169"),
    )

    desc_style = ParagraphStyle(
        "DishDesc",
        fontName=base_font,
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#4A5568"),
    )

    price_style = ParagraphStyle(
        "DishPrice",
        fontName=bold_font,
        fontSize=10.5,
        leading=13,
        alignment=2,  # Right align
        textColor=colors.HexColor("#1A202C"),
    )

    footer_style = ParagraphStyle(
        "MenuFooter",
        fontName=base_font,
        fontSize=8,
        leading=10,
        alignment=1,
        textColor=colors.HexColor("#A0AEC0"),
    )

    story = []

    # Restaurant Header
    story.append(Paragraph(restaurant.name.upper(), title_style))
    if restaurant.tagline:
        story.append(Paragraph(restaurant.tagline, tagline_style))

    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#CBD5E0"), spaceAfter=14))

    # Group by category
    categorized = group_dishes_by_category(dishes)

    for cat_name, cat_dishes in categorized.items():
        category_elements = []
        category_elements.append(Paragraph(cat_name.upper(), category_style))
        category_elements.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceAfter=6))

        for dish in cat_dishes:
            price_text = format_price(dish.price, symbol=currency_prefix)
            
            # Left block: Title, dietary tag, description, ingredients
            desc_text = dish.description_en or "Freshly prepared to order."
            left_flowables = [
                Paragraph(dish.name, dish_name_style),
            ]
            if dish.dietary:
                left_flowables.append(Paragraph(f"• {dish.dietary}", dietary_style))
            
            left_flowables.append(Paragraph(desc_text, desc_style))
            if dish.ingredients:
                left_flowables.append(Paragraph(f"<i>Ingredients: {dish.ingredients}</i>", ParagraphStyle(
                    "IngStyle", fontName=base_font, fontSize=7, leading=9, textColor=colors.HexColor("#718096")
                )))

            # Table row for clean alignment: [Left Content, Price]
            row_data = [
                left_flowables,
                Paragraph(price_text, price_style),
            ]

            dish_table = Table(
                [row_data],
                colWidths=[420, 100],
            )
            dish_table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
            ]))

            category_elements.append(dish_table)

        story.append(KeepTogether(category_elements))
        story.append(Spacer(1, 10))

    # Footer note
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#E2E8F0"), spaceAfter=6))
    story.append(Paragraph("Handcrafted with MenuMind AI • Taxes and charges as applicable", footer_style))

    doc.build(story)
    return buffer.getvalue()


def generate_unicode_html_menu(
    restaurant: RestaurantInfo,
    dishes: List[DishItem],
    language: str = "en",
) -> str:
    """
    Generate an authentic, print-optimized Unicode HTML menu.
    Leverages Google Fonts for perfect Indic (Tamil & Devanagari) glyph shaping
    and includes @media print CSS for standard A4 browser printing / Save to PDF.
    """
    categorized = group_dishes_by_category(dishes)
    lang_labels = {
        "en": "English Menu",
        "ta": "தமிழ் மெனு (Tamil Menu)",
        "hi": "हिन्दी मेनू (Hindi Menu)",
    }
    lang_display = lang_labels.get(language, "Multilingual Menu")

    # Build category sections
    sections_html = []
    for cat_name, cat_dishes in categorized.items():
        dishes_html = []
        for d in cat_dishes:
            desc = d.get_description(language)
            diet_badge = ""
            if d.dietary:
                is_veg = "veg" in d.dietary.lower() and "non" not in d.dietary.lower()
                badge_color = "#2e7d32" if is_veg else "#c62828"
                diet_badge = f'<span class="diet-badge" style="color: {badge_color}; border-color: {badge_color};">{d.dietary}</span>'

            ing_html = ""
            if d.ingredients:
                ing_html = f'<div class="dish-ingredients">Ingredients: {d.ingredients}</div>'

            price_str = format_price(d.price, symbol="₹")

            dishes_html.append(f"""
            <div class="dish-card">
                <div class="dish-header">
                    <div class="dish-title-group">
                        <span class="dish-name">{d.name}</span>
                        {diet_badge}
                    </div>
                    <span class="dish-price">{price_str}</span>
                </div>
                <div class="dish-desc">{desc}</div>
                {ing_html}
            </div>
            """)

        sections_html.append(f"""
        <section class="category-section">
            <h2 class="category-title">{cat_name}</h2>
            <div class="category-divider"></div>
            <div class="dishes-grid">
                {''.join(dishes_html)}
            </div>
        </section>
        """)

    html_content = f"""<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{restaurant.name} - {lang_display}</title>
    <!-- High quality Unicode fonts with full Indic shaping support -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;700&family=Inter:wght@400;500;600&family=Noto+Sans+Devanagari:wght@400;500;600;700&family=Noto+Sans+Tamil:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --primary: #8b181b;
            --accent: #d4a373;
            --text-dark: #1f2937;
            --text-muted: #4b5563;
            --card-bg: #fffbf5;
            --border-color: #eedcc9;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }}
        body {{
            font-family: 'Inter', 'Noto Sans Tamil', 'Noto Sans Devanagari', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            color: var(--text-dark);
            background-color: #f7f3ee;
            padding: 24px;
            line-height: 1.5;
        }}
        .action-bar {{
            max-width: 820px;
            margin: 0 auto 20px auto;
            background: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 12px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: 0 2px 4px rgba(0,0,0,0.04);
        }}
        .print-btn {{
            background: #8b181b;
            color: #ffffff;
            border: none;
            padding: 10px 18px;
            border-radius: 6px;
            font-weight: 600;
            font-size: 14px;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }}
        .print-btn:hover {{
            background: #6e1315;
        }}
        .print-notice {{
            font-size: 13px;
            color: #4b5563;
        }}
        .menu-container {{
            max-width: 820px;
            margin: 0 auto;
            background: #ffffff;
            padding: 48px;
            box-shadow: 0 4px 14px rgba(0,0,0,0.06);
            border: 1px solid var(--border-color);
            border-radius: 4px;
        }}
        .menu-header {{
            text-align: center;
            border-bottom: 2px solid var(--accent);
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .restaurant-title {{
            font-family: 'Cinzel', serif;
            font-size: 32px;
            letter-spacing: 1px;
            color: var(--primary);
            text-transform: uppercase;
            margin-bottom: 6px;
        }}
        .restaurant-tagline {{
            font-size: 14px;
            font-style: italic;
            color: var(--text-muted);
            margin-bottom: 10px;
        }}
        .language-badge {{
            display: inline-block;
            background: #fbf0ea;
            color: var(--primary);
            font-size: 11px;
            font-weight: 600;
            padding: 3px 10px;
            border-radius: 12px;
            border: 1px solid #f2c7b5;
        }}
        .category-section {{
            margin-bottom: 28px;
            page-break-inside: avoid;
        }}
        .category-title {{
            font-size: 17px;
            font-weight: 700;
            color: var(--primary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 4px;
        }}
        .category-divider {{
            height: 2px;
            background: linear-gradient(to right, var(--accent), transparent);
            margin-bottom: 14px;
        }}
        .dishes-grid {{
            display: flex;
            flex-direction: column;
            gap: 14px;
        }}
        .dish-card {{
            padding: 8px 0;
            border-bottom: 1px dashed var(--border-color);
            page-break-inside: avoid;
        }}
        .dish-card:last-child {{
            border-bottom: none;
        }}
        .dish-header {{
            display: flex;
            justify-content: space-between;
            align-items: baseline;
            margin-bottom: 4px;
        }}
        .dish-title-group {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .dish-name {{
            font-weight: 600;
            font-size: 15px;
            color: var(--text-dark);
        }}
        .diet-badge {{
            font-size: 10px;
            font-weight: 600;
            padding: 1px 6px;
            border-radius: 4px;
            border: 1px solid;
            background: #fff;
        }}
        .dish-price {{
            font-weight: 700;
            font-size: 15px;
            color: var(--text-dark);
            white-space: nowrap;
        }}
        .dish-desc {{
            font-size: 13px;
            color: var(--text-muted);
            margin-bottom: 3px;
            line-height: 1.4;
        }}
        .dish-ingredients {{
            font-size: 11px;
            color: #6b7280;
            font-style: italic;
        }}
        .menu-footer {{
            text-align: center;
            font-size: 11px;
            color: #9ca3af;
            border-top: 1px solid var(--border-color);
            padding-top: 16px;
            margin-top: 36px;
        }}

        /* Print Media Styling for high-resolution A4 / Save as PDF */
        @media print {{
            body {{
                background-color: #ffffff;
                padding: 0;
            }}
            .action-bar {{
                display: none !important;
            }}
            .menu-container {{
                box-shadow: none;
                border: none;
                padding: 0;
                max-width: 100%;
            }}
            @page {{
                size: A4;
                margin: 15mm;
            }}
            .category-section, .dish-card {{
                page-break-inside: avoid;
                break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <div class="action-bar">
        <div class="print-notice">
            <strong>{lang_display}</strong> • Ready for high-resolution printing or PDF export.
        </div>
        <button class="print-btn" onclick="window.print()">
            🖨️ Print / Save as PDF
        </button>
    </div>

    <main class="menu-container">
        <header class="menu-header">
            <h1 class="restaurant-title">{restaurant.name}</h1>
            {f'<p class="restaurant-tagline">{restaurant.tagline}</p>' if restaurant.tagline else ''}
            <span class="language-badge">{lang_display}</span>
        </header>

        {''.join(sections_html)}

        <footer class="menu-footer">
            <p>MenuMind AI • 100% Offline-First AI Menu Studio • Prices inclusive of applicable GST</p>
        </footer>
    </main>
</body>
</html>
"""
    return html_content
