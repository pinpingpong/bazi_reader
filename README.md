# BaZi Reader 八字

An AI-powered Four Pillars of Destiny (BaZi) calculator and interpreter built with Streamlit and the Google Gemini API.

Users enter their birth date, time, and gender. The app calculates their full BaZi chart — including hidden stems, special stars, and 10-year luck pillars — then uses Gemini to deliver a multi-section AI reading, annual forecast, compatibility analysis, and an interactive chart Q&A.

Live demo: *https://px-bazireader.streamlit.app/*

---

## Features

**Chart (Tab 1)**
- Four Pillars calculated with exact fractional C-value solar term boundaries (20th and 21st century)
- Colour-coded pillar cards showing heavenly stem, earthly branch, element, animal, and hidden stems (藏干)
- Element balance across all eight characters
- Special stars detection: Nobleman (天乙贵人), Peach Blossom (桃花), Academic (文昌), Travelling Horse (驿马), Canopy (华盖)
- Shareable URL (birth info encoded in query params) and text export

**Luck Pillars (Tab 2)**
- Full Da Yun (大运) calculation — 8 ten-year luck pillars with start ages and calendar years
- Direction (forward/backward) based on gender and year stem polarity
- Current active pillar highlighted

**AI Insights (Tab 3)**
- Natal reading: Character, Strengths, Challenges, Career, Relationships, Health, Current Luck Period
- Annual forecast: year theme, opportunities, cautions, and month-by-month breakdown for the rest of the year
- Both sections generated on demand; regeneratable

**Compatibility (Tab 4)**
- Enter a second person's birth details
- AI compares both charts: synergies, friction points, romantic dynamics, career compatibility, and advice

**Chat (Tab 5)**
- Conversational Q&A with your chart as context
- Full multi-turn memory within the session
- Ask about any aspect: destiny, specific years, relationships, health, career

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
- **Month pillar** — exact fractional solar term boundaries using century-specific C-values
- **Day pillar** — sequential 60-cycle count from January 1, 1900
- **Hour pillar** — two-hour earthly branch segments; stem derived from day stem
- **Hidden stems** — all藏干 (main, mid, minor qi) for each branch
- **Special stars** — Nobleman, Peach Blossom, Academic, Travelling Horse, Canopy
- **Da Yun** — 8 ten-year luck pillars via solar term day-count; direction determined by gender + year polarity
- **Current pillars** — live solar year and month pillar for forecast context

### AI Analysis (`app.py`)

Four separate Gemini prompts handle: natal reading, annual/monthly forecast, compatibility comparison, and chat. Each prompt includes the full chart context (pillars, hidden stems, Da Yun, special stars). Chat maintains full multi-turn history within the session via Gemini's native chat API.

---

## Notes

- All times are interpreted as **UTC+8** (Singapore, Malaysia, Hong Kong, China). No longitude correction is applied.
- For dates in January or early February, the solar year may be treated as the previous year depending on whether Lichun has passed.
- This app is for entertainment and cultural reference. It is not a substitute for professional advice.

---

## Related

- Original HTML calculator: `bazi_calculator.html` (standalone, no AI)
- Portfolio: *(add your Vercel portfolio URL here)*
