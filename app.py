"""
MenuMind AI — Offline-First Multilingual AI Menu Creation Studio for Indian Restaurants.
Built with Streamlit, Pydantic, Pandas, and Ollama local inference.
"""

import io
import streamlit as st

from ai_engine import DEFAULT_MODEL, DEFAULT_OLLAMA_HOST, OllamaClient
from menu_utils import (
    export_dishes_to_csv,
    format_price,
    generate_sample_csv_content,
    group_dishes_by_category,
    parse_and_validate_csv,
)
from pdf_export import (
    check_indic_pdf_capability,
    generate_english_pdf,
    generate_unicode_html_menu,
)
from schemas import DishInput, DishItem, RestaurantInfo


# Page Configuration
st.set_page_config(
    page_title="MenuMind AI — Multilingual Menu Studio",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom High-Contrast, Restaurant-Grade CSS
st.markdown("""
<style>
    /* Clean, modern typography and spacing */
    .hero-container {
        background: linear-gradient(135deg, #2b110b 0%, #4a1913 50%, #1e130c 100%);
        color: #ffffff;
        padding: 24px 32px;
        border-radius: 12px;
        margin-bottom: 24px;
        border-left: 6px solid #e08b29;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    }
    .hero-title {
        font-size: 32px;
        font-weight: 800;
        margin-bottom: 6px;
        color: #fff6eb;
        letter-spacing: -0.5px;
    }
    .hero-subtitle {
        font-size: 15px;
        color: #f7d2b2;
        max-width: 850px;
        line-height: 1.5;
    }
    .badge-tag {
        display: inline-block;
        background: rgba(224, 139, 41, 0.25);
        color: #ffc97a;
        font-size: 11px;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 999px;
        border: 1px solid rgba(224, 139, 41, 0.5);
        margin-top: 10px;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .status-card {
        padding: 12px 16px;
        border-radius: 8px;
        font-size: 13px;
        margin-bottom: 12px;
    }
    .status-online {
        background-color: #f0fdf4;
        border: 1px solid #bbf7d0;
        color: #166534;
    }
    .status-offline {
        background-color: #fef2f2;
        border: 1px solid #fecaca;
        color: #991b1b;
    }
    .dish-preview-card {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 8px;
        padding: 14px 18px;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
    }
    .dish-preview-name {
        font-size: 16px;
        font-weight: 700;
        color: #111827;
    }
    .dish-preview-price {
        font-size: 16px;
        font-weight: 800;
        color: #92400e;
    }
    .diet-badge-green {
        background-color: #ecfdf5;
        color: #065f46;
        border: 1px solid #a7f3d0;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
    }
    .diet-badge-red {
        background-color: #fef2f2;
        color: #991b1b;
        border: 1px solid #fecaca;
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 11px;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        font-weight: 600;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)


# Initialize Session State
def init_session_state():
    if "restaurant_info" not in st.session_state:
        st.session_state.restaurant_info = RestaurantInfo(
            name="Saffron & Spice Kitchen",
            tagline="Authentic Flavors, Handcrafted with Love",
        )

    if "dishes" not in st.session_state:
        # Pre-populate with realistic 10-dish sample
        sample_csv = generate_sample_csv_content()
        report = parse_and_validate_csv(sample_csv)
        st.session_state.dishes = report.valid_dishes

    if "ollama_host" not in st.session_state:
        st.session_state.ollama_host = DEFAULT_OLLAMA_HOST

    if "ollama_model" not in st.session_state:
        st.session_state.ollama_model = DEFAULT_MODEL

    if "target_language" not in st.session_state:
        st.session_state.target_language = "en"

    if "edit_dish_id" not in st.session_state:
        st.session_state.edit_dish_id = None


init_session_state()


# Sidebar: Restaurant Profile & AI Engine Status
with st.sidebar:
    st.markdown("### 🏢 Restaurant Profile")
    rest_name = st.text_input(
        "Restaurant Name",
        value=st.session_state.restaurant_info.name,
        help="Appears on menus and headers",
    )
    rest_tagline = st.text_input(
        "Tagline (Optional)",
        value=st.session_state.restaurant_info.tagline or "",
        help="Short tagline or specialty",
    )
    if rest_name != st.session_state.restaurant_info.name or rest_tagline != st.session_state.restaurant_info.tagline:
        st.session_state.restaurant_info.name = rest_name.strip() or "My Restaurant"
        st.session_state.restaurant_info.tagline = rest_tagline.strip()

    st.markdown("---")
    st.markdown("### 🤖 Local Ollama Engine")
    
    ollama_host_input = st.text_input(
        "Ollama Host URL",
        value=st.session_state.ollama_host,
        help="Default local endpoint: http://127.0.0.1:11434",
    )
    ollama_model_input = st.text_input(
        "Model Name",
        value=st.session_state.ollama_model,
        help="Recommended: qwen3:4b (or qwen2.5:3b / llama3.2:3b)",
    )
    st.session_state.ollama_host = ollama_host_input.strip()
    st.session_state.ollama_model = ollama_model_input.strip()

    client = OllamaClient(host=st.session_state.ollama_host, model=st.session_state.ollama_model)
    is_online, status_msg, available_models = client.check_health()

    if is_online:
        st.markdown(f"""
        <div class="status-card status-online">
            <strong>🟢 Ollama Online</strong><br>
            {status_msg}
        </div>
        """, unsafe_allow_html=True)
        if available_models:
            with st.expander("Available Models on Host"):
                for m in available_models:
                    st.code(m, language="text")
    else:
        st.markdown(f"""
        <div class="status-card status-offline">
            <strong>🔴 Ollama Offline</strong><br>
            {status_msg}
        </div>
        """, unsafe_allow_html=True)
        with st.expander("🛠️ How to start Ollama"):
            st.markdown("""
            1. Install Ollama from [ollama.com](https://ollama.com).
            2. Run in terminal:
               ```powershell
               ollama run qwen3:4b
               ```
            3. Verify endpoint at `http://127.0.0.1:11434`.
            """)

    st.markdown("---")
    st.markdown("### 🔤 Indic Script PDF Check")
    has_indic_pdf, indic_msg = check_indic_pdf_capability()
    if has_indic_pdf:
        st.success("🟢 Indic PDF Engine Active")
    else:
        st.info("ℹ️ **Rendering Notice:** Standard PDF engines (ReportLab) lack Indic OpenType ligature shaping. High-fidelity Unicode HTML export with print CSS is provided for Tamil and Hindi menus.")

    st.markdown("---")
    st.markdown("### ⚡ Quick Actions")
    if st.button("🔄 Reset to 10-Dish Sample", use_container_width=True):
        report = parse_and_validate_csv(generate_sample_csv_content())
        st.session_state.dishes = report.valid_dishes
        st.rerun()

    if st.button("🗑️ Clear All Dishes", use_container_width=True):
        st.session_state.dishes = []
        st.rerun()


# Hero Header
st.markdown("""
<div class="hero-container">
    <div class="hero-title">🍽️ MenuMind AI</div>
    <div class="hero-subtitle">
        Offline-first multilingual AI menu studio tailored for small Indian restaurants. 
        Generate mouth-watering, fact-grounded descriptions in <strong>English, தமிழ் (Tamil), and हिन्दी (Hindi)</strong> 
        using local Ollama inference. 100% private, zero cloud fees, zero data leaks.
    </div>
    <div class="badge-tag">🔒 Private • 100% Offline • Hacktoberfest 2026</div>
</div>
""", unsafe_allow_html=True)


# Main Application Tabs
tab_csv, tab_ai, tab_preview, tab_export = st.tabs([
    "📋 1. Dishes & CSV Import",
    "🤖 2. AI Description Studio",
    "🍽️ 3. Live Menu Preview",
    "📦 4. Export & Print Studio",
])


# ==============================================================================
# TAB 1: DISHES & CSV IMPORT
# ==============================================================================
with tab_csv:
    col_upload, col_sample = st.columns([3, 1])
    with col_sample:
        st.download_button(
            label="📥 Download Sample CSV",
            data=generate_sample_csv_content(),
            file_name="menumind_sample_menu.csv",
            mime="text/csv",
            help="Download a pre-formatted template with headers: name, category, price, ingredients, dietary",
            use_container_width=True,
        )

    with col_upload:
        uploaded_file = st.file_uploader(
            "Import Menu via CSV",
            type=["csv"],
            help="Upload a CSV with columns: name, category, price, ingredients, dietary",
        )

    if uploaded_file is not None:
        try:
            content = uploaded_file.getvalue().decode("utf-8")
            report = parse_and_validate_csv(content)
            
            if report.errors:
                st.error(f"Found {len(report.errors)} issue(s) during CSV validation:")
                for err in report.errors:
                    st.markdown(f"- ⚠️ {err}")
            
            if report.valid_dishes:
                st.success(f"Successfully validated {len(report.valid_dishes)} dish(es) from CSV.")
                if st.button(f"Load {len(report.valid_dishes)} Dishes into Studio", type="primary"):
                    st.session_state.dishes = report.valid_dishes
                    st.rerun()
        except Exception as e:
            st.error(f"Error parsing uploaded file: {str(e)}")

    st.markdown("---")

    # Add / Edit Dish Form
    with st.expander("➕ Add a New Dish Manually", expanded=len(st.session_state.dishes) == 0):
        with st.form("manual_add_dish_form", clear_on_submit=True):
            f_col1, f_col2, f_col3 = st.columns([2, 1, 1])
            with f_col1:
                new_name = st.text_input("Dish Name *", placeholder="e.g. Malai Kofta")
            with f_col2:
                new_cat = st.text_input("Category", value="Mains", placeholder="e.g. Mains, Starters")
            with f_col3:
                new_price = st.text_input("Price (₹) *", placeholder="e.g. 280")

            new_ing = st.text_area(
                "Ingredients (Strictly Grounded Facts) *",
                placeholder="e.g. Paneer dumplings, potato, cashew-cream tomato gravy, cardamom, kasuri methi",
                help="Only mention real ingredients. The AI will never invent ingredients outside this list.",
            )
            new_diet = st.text_input(
                "Dietary Classification (Optional)",
                placeholder="e.g. Vegetarian, Gluten-Free, Non-Vegetarian",
            )

            submit_add = st.form_submit_button("Add Dish to Menu", type="primary")
            if submit_add:
                try:
                    dish_in = DishInput(
                        name=new_name,
                        category=new_cat,
                        price=new_price,
                        ingredients=new_ing,
                        dietary=new_diet,
                    )
                    new_item = DishItem(
                        id=dish_in.id,
                        name=dish_in.name,
                        category=dish_in.category,
                        price=dish_in.price,
                        ingredients=dish_in.ingredients,
                        dietary=dish_in.dietary,
                    )
                    st.session_state.dishes.append(new_item)
                    st.success(f"Added '{new_item.name}' to the menu!")
                    st.rerun()
                except Exception as ve:
                    st.error(f"Validation error: {str(ve)}")

    # Current Dishes Table / Manager
    st.markdown(f"### Current Menu Items ({len(st.session_state.dishes)} dishes)")
    if not st.session_state.dishes:
        st.info("No dishes on the menu yet. Click 'Add a New Dish Manually' or import a CSV.")
    else:
        for idx, dish in enumerate(st.session_state.dishes):
            with st.container():
                c1, c2, c3, c4, c5 = st.columns([3, 2, 2, 4, 1.5])
                with c1:
                    st.markdown(f"**{idx + 1}. {dish.name}**")
                    if dish.dietary:
                        st.caption(f"🏷️ {dish.dietary}")
                with c2:
                    st.markdown(f"📂 {dish.category}")
                with c3:
                    st.markdown(f"**{format_price(dish.price)}**")
                with c4:
                    st.caption(f"🧂 {dish.ingredients[:60]}..." if len(dish.ingredients) > 60 else f"🧂 {dish.ingredients}")
                with c5:
                    if st.button("🗑️ Delete", key=f"del_{dish.id}_{idx}"):
                        st.session_state.dishes.pop(idx)
                        st.rerun()
                st.markdown("<hr style='margin: 4px 0 8px 0; border: none; border-top: 1px solid #f3f4f6;'>", unsafe_allow_html=True)


# ==============================================================================
# TAB 2: AI DESCRIPTION STUDIO
# ==============================================================================
with tab_ai:
    st.markdown("### 🤖 Multilingual AI Copywriter")
    st.markdown("""
    Generate concise, appetizing menu descriptions grounded **strictly in your ingredient facts**. 
    Prices and dish names are strictly preserved outside the AI output to eliminate any possibility of hallucination.
    """)

    col_lang, col_overwrite, col_action = st.columns([2, 2, 3])
    with col_lang:
        target_lang = st.selectbox(
            "Select Target Language",
            options=["en", "ta", "hi"],
            format_func=lambda x: {"en": "English", "ta": "தமிழ் (Tamil)", "hi": "हिन्दी (Hindi)"}[x],
            index=["en", "ta", "hi"].index(st.session_state.target_language),
        )
        st.session_state.target_language = target_lang

    with col_overwrite:
        overwrite_edited = st.checkbox(
            "Regenerate dishes with manual edits",
            value=False,
            help="If unchecked, previously edited descriptions will be safely preserved.",
        )

    with col_action:
        st.write("")
        st.write("")
        generate_all_btn = st.button(
            f"✨ Generate Descriptions in {dict(en='English', ta='Tamil', hi='Hindi')[target_lang]}",
            type="primary",
            use_container_width=True,
            disabled=len(st.session_state.dishes) == 0,
        )

    if generate_all_btn:
        client = OllamaClient(host=st.session_state.ollama_host, model=st.session_state.ollama_model)
        online, msg, _ = client.check_health()
        if not online:
            st.error(f"Cannot generate: {msg}")
        else:
            progress_bar = st.progress(0.0)
            status_text = st.empty()

            def update_progress(ratio, text):
                progress_bar.progress(ratio)
                status_text.text(text)

            with st.spinner(f"Contacting local Ollama ({st.session_state.ollama_model})..."):
                success_n, skipped_n, errors = client.batch_generate(
                    dishes=st.session_state.dishes,
                    language=target_lang,
                    overwrite_user_edited=overwrite_edited,
                    progress_callback=update_progress,
                )

            progress_bar.empty()
            status_text.empty()

            if success_n > 0:
                st.success(f"Generated descriptions for {success_n} dish(es)!")
            if skipped_n > 0:
                st.info(f"Skipped {skipped_n} dish(es) with manual edits to preserve owner customizations.")
            if errors:
                st.warning(f"Failed to generate for {len(errors)} dish(es):")
                for e in errors:
                    st.markdown(f"- ⚠️ {e}")
            st.rerun()

    st.markdown("---")
    st.markdown(f"#### Side-by-Side Review & In-Place Editing ({dict(en='English', ta='Tamil', hi='Hindi')[target_lang]})")

    if not st.session_state.dishes:
        st.info("No dishes available to edit. Add dishes in Tab 1.")
    else:
        for idx, dish in enumerate(st.session_state.dishes):
            with st.container():
                left_col, right_col = st.columns([1, 1])
                with left_col:
                    st.markdown(f"##### {idx + 1}. {dish.name} — `{format_price(dish.price)}`")
                    st.markdown(f"**Category:** {dish.category}")
                    if dish.dietary:
                        st.markdown(f"**Dietary:** `{dish.dietary}`")
                    st.markdown(f"**Ingredients:** *{dish.ingredients}*")

                with right_col:
                    curr_desc = dish.get_description(target_lang)
                    is_edited = dish.is_user_edited.get(target_lang, False)
                    edit_label = "✏️ Owner-Edited" if is_edited else "🤖 AI Generated"
                    
                    edited_text = st.text_area(
                        f"Description ({edit_label})",
                        value=curr_desc,
                        key=f"desc_{dish.id}_{target_lang}_{idx}",
                        height=100,
                        help="Edit this description directly. Your manual edits will be preserved.",
                    )

                    col_save, col_single_gen = st.columns([1, 1])
                    with col_save:
                        if edited_text != curr_desc:
                            if st.button("💾 Save Edit", key=f"save_{dish.id}_{target_lang}_{idx}"):
                                dish.set_description(target_lang, edited_text, user_edited=True)
                                st.toast(f"Saved description for {dish.name}!")
                                st.rerun()
                    with col_single_gen:
                        if st.button("🔄 Regenerate Single", key=f"regen_{dish.id}_{target_lang}_{idx}"):
                            client = OllamaClient(host=st.session_state.ollama_host, model=st.session_state.ollama_model)
                            ok, new_desc, err = client.generate_description(
                                dish_name=dish.name,
                                ingredients=dish.ingredients,
                                dietary=dish.dietary,
                                language=target_lang,
                            )
                            if ok:
                                dish.set_description(target_lang, new_desc, user_edited=False)
                                st.success("Regenerated!")
                                st.rerun()
                            else:
                                st.error(err)

                st.markdown("<hr style='margin: 12px 0 16px 0; border: none; border-top: 1px solid #e5e7eb;'>", unsafe_allow_html=True)


# ==============================================================================
# TAB 3: LIVE MENU PREVIEW
# ==============================================================================
with tab_preview:
    st.markdown("### 🍽️ Grouped Menu Preview")

    preview_lang = st.selectbox(
        "Preview Language",
        options=["en", "ta", "hi"],
        format_func=lambda x: {"en": "English", "ta": "தமிழ் (Tamil)", "hi": "हिन्दी (Hindi)"}[x],
        key="preview_lang_select",
    )

    st.markdown(f"""
    <div style="text-align: center; margin: 20px 0 30px 0;">
        <h1 style="color: #8b181b; font-family: serif; text-transform: uppercase; margin-bottom: 4px;">{st.session_state.restaurant_info.name}</h1>
        <p style="color: #6b7280; font-style: italic; font-size: 15px;">{st.session_state.restaurant_info.tagline or ''}</p>
        <span style="background: #fef3c7; color: #92400e; padding: 2px 10px; border-radius: 12px; font-size: 12px; font-weight: 600;">
            {dict(en='English Menu', ta='தமிழ் மெனு', hi='हिन्दी मेनू')[preview_lang]}
        </span>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.dishes:
        st.info("No dishes to display yet. Add some in Tab 1.")
    else:
        categorized = group_dishes_by_category(st.session_state.dishes)
        for cat_name, cat_dishes in categorized.items():
            st.markdown(f"#### 📂 {cat_name.upper()}")
            st.markdown("<div style='height: 2px; background: #e08b29; margin-bottom: 12px;'></div>", unsafe_allow_html=True)

            for d in cat_dishes:
                desc = d.get_description(preview_lang) or "Freshly prepared to order."
                is_veg = "veg" in d.dietary.lower() and "non" not in d.dietary.lower()
                badge_class = "diet-badge-green" if is_veg else "diet-badge-red"
                diet_badge_html = f'<span class="{badge_class}">{d.dietary}</span>' if d.dietary else ""

                st.markdown(f"""
                <div class="dish-preview-card">
                    <div style="display: flex; justify-content: space-between; align-items: baseline;">
                        <div>
                            <span class="dish-preview-name">{d.name}</span>
                            &nbsp;{diet_badge_html}
                        </div>
                        <span class="dish-preview-price">{format_price(d.price)}</span>
                    </div>
                    <div style="color: #4b5563; font-size: 13.5px; margin-top: 4px;">{desc}</div>
                    <div style="color: #9ca3af; font-size: 11px; font-style: italic; margin-top: 2px;">Ingredients: {d.ingredients}</div>
                </div>
                """, unsafe_allow_html=True)


# ==============================================================================
# TAB 4: EXPORT & PRINT STUDIO
# ==============================================================================
with tab_export:
    st.markdown("### 📦 Export & Print Studio")
    st.markdown("Download publication-ready menus for print or online delivery.")

    exp_col1, exp_col2 = st.columns([1, 1])

    with exp_col1:
        st.markdown("#### 📄 English PDF (ReportLab)")
        st.markdown("""
        - Formatted for standard A4 commercial print.
        - Verified TrueType Indian Rupee symbol (`₹`) rendering.
        - Categorized, structured, and factually grounded.
        """)

        if st.session_state.dishes:
            try:
                pdf_bytes = generate_english_pdf(
                    restaurant=st.session_state.restaurant_info,
                    dishes=st.session_state.dishes,
                )
                st.download_button(
                    label="📥 Download English PDF Menu",
                    data=pdf_bytes,
                    file_name=f"{st.session_state.restaurant_info.name.replace(' ', '_').lower()}_english_menu.pdf",
                    mime="application/pdf",
                    type="primary",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Error compiling English PDF: {str(e)}")
        else:
            st.info("Add dishes to generate PDF.")

    with exp_col2:
        st.markdown("#### 🌐 Multilingual Unicode HTML Studio")
        st.markdown("""
        - **100% Authentic Indic Shaping**: Tamil and Hindi ligatures and conjuncts shaped with native perfection via Google Noto Fonts.
        - **Print-to-PDF**: Styled with `@media print` CSS for instant 1-click A4 PDF generation via browser (Ctrl + P).
        """)

        html_lang = st.selectbox(
            "Export Language for Unicode HTML",
            options=["en", "ta", "hi"],
            format_func=lambda x: {"en": "English", "ta": "தமிழ் (Tamil)", "hi": "हिन्दी (Hindi)"}[x],
            key="export_html_lang",
        )

        if st.session_state.dishes:
            html_content = generate_unicode_html_menu(
                restaurant=st.session_state.restaurant_info,
                dishes=st.session_state.dishes,
                language=html_lang,
            )

            st.download_button(
                label=f"📥 Download {dict(en='English', ta='Tamil', hi='Hindi')[html_lang]} HTML Menu",
                data=html_content,
                file_name=f"{st.session_state.restaurant_info.name.replace(' ', '_').lower()}_{html_lang}_menu.html",
                mime="text/html",
                use_container_width=True,
            )

            with st.expander("👁️ Preview HTML Code"):
                st.code(html_content[:600] + "\n\n... [truncated for preview] ...", language="html")

    st.markdown("---")
    st.markdown("#### 📊 Export Data as CSV")
    if st.session_state.dishes:
        csv_data = export_dishes_to_csv(st.session_state.dishes)
        st.download_button(
            label="📥 Download All Dishes with Multilingual Descriptions (CSV)",
            data=csv_data,
            file_name=f"{st.session_state.restaurant_info.name.replace(' ', '_').lower()}_full_menu.csv",
            mime="text/csv",
            use_container_width=True,
        )
