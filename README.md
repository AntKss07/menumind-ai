# MenuMind AI 🍽️
**Offline-First Multilingual AI Menu Creation Studio for Indian Restaurants**

*Hacktoberfest 2026 — Week 2 Project*

---

## 📌 Problem & Target Customers

Small, independent Indian restaurants, dhabas, cloud kitchens, and regional eateries often struggle to create professional, appetizing, multilingual menus. 
- **The Language Barrier**: Indian dining customers come from diverse linguistic backgrounds (English, Tamil, Hindi, etc.). Small restaurant owners rarely have the budget to hire multilingual copywriters or translators.
- **The Cloud AI Dilemma**: Cloud AI APIs (OpenAI, Anthropic, Gemini) require paid subscriptions, recurring per-token charges, reliable high-speed internet, and send sensitive business recipes/sales data to remote servers.
- **The Hallucination Danger**: Generic AI frequently hallucinates ingredients (e.g. adding beef or peanuts where they don't belong, creating severe religious or allergen liabilities), alters dish names, or hallucinates medical health claims.
- **Complex Script Shaping in PDF**: Indic scripts (Tamil, Hindi) require OpenType font ligature and conjunct shaping (GSUB/GPOS). Standard PDF libraries often print detached vowel signs or garbled characters.

**Target Customers:**
- Family-run Indian restaurants and regional diners (South Indian tiffin centers, North Indian dhabas, Mughlai grills).
- Cloud kitchen operators managing multi-brand menus.
- Rural or suburban eateries with intermittent internet connectivity.
- IT service freelancers setting up localized IT systems for local restaurants.

---

## ✨ Core Features

1. **Deterministic Dish Fact Grounding**: The AI is strictly constrained to the ingredients and dietary metadata provided by the owner. It will **never** invent ingredients, allergens, or preparation methods.
2. **True Multilingual Menu Copywriting**: Generates natural, appetizing, culturally resonant descriptions in:
   - **English**
   - **தமிழ் (Tamil)**
   - **हिन्दी (Hindi)**
3. **100% Price & Name Preservation**: Numeric prices and dish names are preserved externally outside LLM tokens, eliminating price hallucinations or rounding errors.
4. **Offline-First Local Inference**: Powered by local [Ollama](https://ollama.com) models (e.g., `qwen3:4b`, `qwen2.5:3b`, `llama3.2:3b`). Zero cloud fees, zero tracking, complete privacy.
5. **CSV Batch Import & Export**: One-click import with deterministic row validation (identifying empty prices, missing ingredients, format anomalies) and a downloadable sample template.
6. **Side-by-Side Review & In-Place Editing**: Review AI-generated copy side-by-side with original facts; manual edits are tracked and safeguarded against accidental overwrites.
7. **Dual-Format Publication Studio**:
   - **English PDF Menu**: ReportLab-powered A4 print-ready PDF with verified Indian Rupee symbol (`₹`) rendering.
   - **Multilingual Unicode HTML Studio**: High-fidelity HTML export embedding Google Noto Sans fonts with `@media print` CSS for 1-click native browser "Print to PDF" with authentic Tamil and Hindi glyph shaping.
8. **Streamlit State Persistence**: Edits and loaded dishes persist across browser reruns and tab switches using `st.session_state`.
9. **Built-in Realistic Sample Menu**: Includes 10 authentic Indian dishes across Starters, Mains, Breads, Desserts, and Beverages.

---

## 🏗️ Architecture

```
menumind ai/
├── app.py                  # Streamlit frontend & interactive studio tabs
├── ai_engine.py            # Local Ollama client with retry logic & JSON schema validation
├── prompts.py              # Prompt-injection hardened, multilingual templates
├── schemas.py              # Pydantic v2 data models & validation rules
├── menu_utils.py           # CSV import/export, deterministic validation & category grouping
├── pdf_export.py           # ReportLab English PDF & Unicode HTML Print-to-PDF engine
├── sample_data/
│   └── sample_menu.csv     # 10 realistic Indian dishes with ingredients & dietary tags
├── tests/
│   ├── test_csv_validation.py      # CSV validation & price error tests
│   ├── test_schemas_and_models.py  # Pydantic schemas & price preservation tests
│   ├── test_ai_engine.py           # Mocked Ollama generation & retry tests
│   ├── test_pdf_and_html_export.py # PDF & HTML export tests
│   └── test_smoke.py               # End-to-end integration & live daemon check
├── requirements.txt        # Python dependencies
└── README.md               # Documentation & setup guide
```

---

## 💻 Windows Installation Instructions

### Prerequisites
- Python 3.11 or Python 3.12 installed on your Windows system.
- PowerShell or Windows Terminal.

### Step 1: Clone or Navigate to the Repository
```powershell
cd "c:\KSS\PROJECTS\hacktoberfest\menumind ai"
```

### Step 2: Create and Activate a Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Step 3: Install Required Dependencies
```powershell
pip install -r requirements.txt
```

---

## 🦙 Ollama Installation & Local Model Setup

MenuMind AI is completely offline and connects to an Ollama instance running locally.

1. **Download Ollama for Windows**:
   - Visit [ollama.com/download](https://ollama.com/download) and run the Windows installer.
2. **Pull the Recommended Model**:
   - Open PowerShell and run:
     ```powershell
     ollama pull qwen3:4b
     ```
   *(Alternative lightweight models: `ollama pull qwen2.5:3b` or `ollama pull llama3.2:3b`)*
3. **Verify Ollama is Running**:
   - Ollama runs in the background on `http://127.0.0.1:11434`.
   - Test in PowerShell:
     ```powershell
     curl http://127.0.0.1:11434/api/tags
     ```

---

## 🚀 Local Run Instructions

To launch the MenuMind AI Studio:

```powershell
streamlit run app.py
```

The application will open in your default browser at `http://localhost:8501`.

---

## 🧪 Running Automated Tests

All tests run locally using `pytest`. Mocked network responses are used to test all edge cases deterministically without requiring an active GPU:

```powershell
pytest -v
```

### Test Coverage Highlights:
- **CSV parsing & error handling**: Validates missing prices, negative prices, currency symbols (`₹`, `Rs.`), missing ingredients.
- **Price preservation**: Ensures numeric prices are never modified by the AI model.
- **Structured output validation**: Enforces Pydantic model validation on model output.
- **Retry on malformed output**: Simulates broken JSON and verifies 1-retry recovery.
- **Model reasoning filter**: Strips `<think>...</think>` tags and raw markdown code blocks.
- **Prompt injection defense**: Neutralizes delimiter escapes and overrides inside user input.
- **PDF & Unicode export**: Verifies PDF headers (`%PDF-`), Rupee symbols, and Tamil/Hindi Unicode preservation.
- **Live smoke test**: Reports actual live daemon status cleanly.

---

## 📸 Screenshots

*(Placeholders for documentation and demo showcases)*

```
+-----------------------------------------------------------------------------------------+
| [ HERO BANNER: MenuMind AI — Offline-First Multilingual Menu Studio ]                   |
+-----------------------------------------------------------------------------------------+
| [ SIDEBAR ]            | [ TABS: Dishes & CSV | AI Studio | Live Preview | Export ]     |
| - Restaurant Profile   |                                                                |
| - Ollama Online Status |  Paneer Tikka | Starters | ₹260                                |
| - Indic Check Notice   |  EN: Succulent cottage cheese marinated in spiced hung curd... |
| - Reset / Clear menu   |  TA: நறுமண மசாலா தயிரில் ஊறவைத்து வாட்டப்பட்ட பன்னீர் துண்டுகள்... |
|                        |  HI: सुगंधित मसालों और दही में मैरीनेट किया हुआ रोस्टेड पनीर... |
+-----------------------------------------------------------------------------------------+
```

---

## 📝 Example Input & Output

### Input (CSV or Manual Form):
```csv
name,category,price,ingredients,dietary
Masala Dosa,South Indian,140,"Fermented rice and urad dal batter, potatoes, onions, mustard seeds, green chilies, curry leaves, turmeric","Vegetarian, Vegan-friendly"
```

### AI Output (Ground-Truth Only):
- **English**: *"Crispy golden fermented rice-lentil crepe wrapped around a savory, tempered potato and curry leaf masala."*
- **தமிழ் (Tamil)**: *"மொருமொருப்பான பொன்னிற தோசை, நறுமணமிக்க தாளித்த உருளைக்கிழங்கு மசாலாவுடன் பரிமாறப்படுகிறது."*
- **हिन्दी (Hindi)**: *"राई और कढ़ी पत्ते के तड़के वाले स्वादिष्ट आलू भरावन से युक्त सुनहरी और कुरकुरी डोसा।"*
- **Preserved Numerical Price**: `₹140.00` (unchanged).

---

## 💡 Open-Source AI & Privacy Advantages

- **Zero Cloud Costs**: Eliminates SaaS subscriptions ($20–$50/mo), making AI accessible to small rural restaurants.
- **100% Data Sovereignty**: Recipe ingredient ratios, proprietary spice blends, and pricing strategies remain strictly on the restaurant's local computer.
- **Offline Resilience**: Runs during internet outages or in remote areas with zero network connectivity.
- **Reproducibility**: Low temperature (0.2) and strict Pydantic schemas guarantee deterministic output.

---

## ⚠️ Known Limitations & Font Shaping Transparency

- **ReportLab Indic Shaper**: Standard ReportLab does not support complex OpenType glyph shaping (GSUB/GPOS ligatures for Tamil and Devanagari). Rather than outputting broken glyphs, MenuMind AI provides a **High-Fidelity Unicode HTML Studio** with `@media print` CSS. Browsers (Chrome, Edge, Firefox) have native HarfBuzz engines that render Tamil and Hindi glyphs with 100% typographic accuracy.
- **Compute Requirements**: Running a 3B/4B quantized model via Ollama requires 4GB to 8GB of RAM on the host machine.

---

## 💼 Potential One-Time Setup & Service Monetization

Local IT consultants, agency freelancers, and POS vendors can monetize MenuMind AI via:
1. **Turnkey Local Hardware Installation**: Setting up a refurbished mini-PC with Ollama pre-configured for small restaurants ($100–$250 one-time fee).
2. **Custom Menu Template Design**: Creating branded HTML/PDF print stylesheets tailored to the restaurant's aesthetic.
3. **Menu Modernization Services**: Auditing restaurant menus, converting paper menus into structured multilingual CSVs, and generating QR-code web menus.

---

## 🎃 Hacktoberfest 2026 Context

MenuMind AI was built as an open-source submission for Hacktoberfest 2026 (Week 2 Challenge). It addresses digital inclusion for regional Indian businesses through local, privacy-respecting, open-source AI.
