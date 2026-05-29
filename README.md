# BaZi Reader 八字

An AI-powered Four Pillars of Destiny (BaZi) calculator and interpreter built with Streamlit and the Google Gemini API.

Users enter their birth date, time, and gender. The app calculates their four pillars using an advanced fractional solar-term model, then passes the chart to Gemini for a structured reading covering personality, career, relationships, health, and a current-year forecast.

Live demo: *(add your Streamlit Cloud URL here after deployment)*

---

## Features

- Four Pillars calculation using exact fractional C-value solar term boundaries (20th and 21st century)
- Colour-coded pillar cards with heavenly stem, earthly branch, element, and animal
- Element balance chart across all eight characters
- AI reading via Gemini 2.0 Flash — seven sections: Character, Strengths, Challenges, Career, Relationships, Health, and Year Forecast
- Runs locally or on Streamlit Community Cloud

---

## Project Structure

```
bazi_reader/
├── app.py                        # Streamlit UI and Gemini API integration
├── bazi.py                       # Pure Python BaZi calculation logic
├── requirements.txt
├── .env.example                  # Local env template
└── .streamlit/
    └── secrets.toml.example      # Streamlit Cloud secrets template
```

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/your-username/bazi-reader.git
cd bazi-reader
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Add your Gemini API key

Get a free key at [aistudio.google.com](https://aistudio.google.com/app/apikey).

Copy the example file and paste your key:

```bash
cp .env.example .env
```

Open `.env` and set:

```
GEMINI_API_KEY=your_key_here
```

### 4. Run the app

```bash
streamlit run app.py
```

---

## Deploying to Streamlit Community Cloud

1. Push this repo to GitHub (the `.env` file is git-ignored — never commit it)
2. Go to [share.streamlit.io](https://share.streamlit.io) and connect your repo
3. Set the main file path to `app.py`
4. Open **Settings → Secrets** and add:

```toml
GEMINI_API_KEY = "your_key_here"
```

No `.env` file is needed on Streamlit Cloud — the app reads from Streamlit secrets automatically.

---

## How It Works

### BaZi Calculation (`bazi.py`)

- **Year pillar** — derived from the solar year boundary (Lichun, start of spring)
- **Month pillar** — determined by the exact fractional day of each solar term using century-specific C-values
- **Day pillar** — sequential 60-cycle count from January 1, 1900
- **Hour pillar** — two-hour earthly branch segments; hour stem derived from day stem

### AI Analysis (`app.py`)

The four pillars, element counts, and birth metadata are formatted into a structured prompt and sent to `gemini-2.0-flash`. The model returns a reading with seven labelled sections.

---

## Notes

- All times are interpreted as **UTC+8** (Singapore, Malaysia, Hong Kong, China). No longitude correction is applied.
- For dates in January or early February, the solar year may be treated as the previous year depending on whether Lichun has passed.
- This app is for entertainment and cultural reference. It is not a substitute for professional advice.

---

## Related

- Original HTML calculator: `bazi_calculator.html` (standalone, no AI)
- Portfolio: *(add your Vercel portfolio URL here)*
