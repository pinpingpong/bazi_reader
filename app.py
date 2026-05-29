import os
from datetime import date as _Date
import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

from bazi import (
    calculate_bazi, calculate_da_yun, get_special_stars,
    get_hidden_stems, get_current_pillars,
    STEMS, STEMS_EN, STEMS_EL,
    BRANCHES, BR_EN, ANIMALS, BR_EL, BR_POL,
    stem_elem, branch_elem,
)

load_dotenv()

st.set_page_config(page_title="AI BaZi Reader 八字", page_icon="☯", layout="centered")

st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #f8f7f4; }
  [data-testid="stForm"] { background: transparent; border: none; padding: 0; }
  .stButton > button {
    border-radius: 8px; border: 0.5px solid #aaa;
    background: #fff; font-weight: 500;
  }
  .stButton > button:hover { background: #f0eeeb; }
  hr { margin: 1rem 0; }
  [data-testid="stChatMessage"] { background: transparent; }
</style>
""", unsafe_allow_html=True)

# ── Constants ─────────────────────────────────────────────────────────────────
ECOL = {
    "Wood":  {"bg":"#EAF3DE","tx":"#3B6D11","bar":"#639922"},
    "Fire":  {"bg":"#FAECE7","tx":"#993C1D","bar":"#D85A30"},
    "Earth": {"bg":"#FAEEDA","tx":"#854F0B","bar":"#BA7517"},
    "Metal": {"bg":"#F1EFE8","tx":"#5F5E5A","bar":"#888780"},
    "Water": {"bg":"#E6F1FB","tx":"#185FA5","bar":"#378ADD"},
}
DM_DESC = {
    "Yang Wood":  "A great tree — upright, ambitious, always reaching for the sky. Leadership comes naturally.",
    "Yin Wood":   "A flower or vine — graceful, adaptable, tenacious. Bends but never breaks.",
    "Yang Fire":  "The sun — radiant, generous, commanding. Lights up every room.",
    "Yin Fire":   "A candle flame — warm, nurturing, perceptive. Illuminates quietly.",
    "Yang Earth": "A mountain — stable, trustworthy, patient. The bedrock others rely on.",
    "Yin Earth":  "Fertile soil — nurturing, receptive, practical. Makes things grow.",
    "Yang Metal": "A sword — decisive, principled, strong-willed. Cuts through confusion.",
    "Yin Metal":  "A jewel — refined, precise, detail-oriented. Seeks perfection.",
    "Yang Water": "The ocean — vast, deep, philosophical. Absorbs everything, flows everywhere.",
    "Yin Water":  "Morning dew — gentle, intuitive, emotionally perceptive. Feels everything.",
}
STAR_DESC = {
    "Nobleman Star 天乙贵人": "People in power readily help you — mentors, sponsors, helpful strangers appear at key moments.",
    "Peach Blossom 桃花":     "Strong romantic magnetism and social charm. You attract others effortlessly.",
    "Academic Star 文昌":     "Sharp intellect, love of learning, and talent for writing or strategic thinking.",
    "Travelling Horse 驿马":  "Restless energy favouring travel, relocation, and career mobility.",
    "Canopy Star 华盖":       "Spiritual depth, artistic sensitivity, and a tendency toward solitude and introspection.",
}

# ── Session state init ────────────────────────────────────────────────────────
ss = st.session_state
ss.setdefault("form_submitted", False)
ss.setdefault("birth_info", None)
ss.setdefault("chart", None)
ss.setdefault("da_yun", None)
ss.setdefault("stars", None)
ss.setdefault("reading", None)
ss.setdefault("forecast", None)
ss.setdefault("compat_reading", None)
ss.setdefault("chat_display", [])
ss.setdefault("chat_history", [])   # Gemini format


# ── Helpers ───────────────────────────────────────────────────────────────────
def get_api_key() -> str:
    try:
        return st.secrets["GEMINI_API_KEY"]
    except Exception:
        return os.getenv("GEMINI_API_KEY", "")


def gemini_model():
    genai.configure(api_key=get_api_key())
    return genai.GenerativeModel("gemini-flash-latest")


def pillar_card(label, si, bi, is_dm=False):
    se = stem_elem(si)
    c  = ECOL[se]
    border = "2px solid #378ADD" if is_dm else "0.5px solid #ddd"
    lbg    = "#E6F1FB" if is_dm else "#f4f3f0"
    ltx    = "#185FA5" if is_dm else "#999"
    dm_tag = " · Day Master" if is_dm else ""
    hs_html = "".join(
        f'<span style="font-size:9px;padding:1px 5px;border-radius:6px;margin:1px;'
        f'background:{ECOL[stem_elem(idx)]["bg"]};color:{ECOL[stem_elem(idx)]["tx"]}">'
        f'{STEMS[idx]} {w}</span>'
        for idx, w in get_hidden_stems(bi)
    )
    return f"""
    <div style="border:{border};border-radius:12px;overflow:hidden;
                text-align:center;background:#fff;flex:1;min-width:0">
      <div style="font-size:10px;color:{ltx};background:{lbg};
                  padding:5px 0;letter-spacing:.04em">{label}{dm_tag}</div>
      <div style="padding:14px 6px 8px">
        <div style="font-size:30px;line-height:1;margin-bottom:3px">{STEMS[si]}</div>
        <div style="font-size:11px;color:#888">{STEMS_EN[si]}</div>
        <span style="display:inline-block;font-size:10px;font-weight:500;
                     padding:2px 8px;border-radius:12px;margin:4px 0 6px;
                     background:{c['bg']};color:{c['tx']}">{STEMS_EL[si]}</span>
      </div>
      <div style="border-top:0.5px solid #eee;padding:8px 6px 6px;background:#f8f7f4">
        <div style="font-size:24px;line-height:1;margin-bottom:3px">{BRANCHES[bi]}</div>
        <div style="font-size:12px;font-weight:500">{ANIMALS[bi]}</div>
        <div style="font-size:10px;color:#888;margin-top:2px">{BR_EL[bi]} · {BR_POL[bi]}</div>
        <div style="margin-top:5px;display:flex;flex-wrap:wrap;justify-content:center;gap:2px">{hs_html}</div>
      </div>
    </div>"""


def da_yun_card(p, birth_year, is_active):
    si, bi = p["si"], p["bi"]
    c      = ECOL[stem_elem(si)]
    border = "2px solid #378ADD" if is_active else "0.5px solid #ddd"
    lbg    = "#E6F1FB" if is_active else "#f4f3f0"
    ltx    = "#185FA5" if is_active else "#999"
    sy, ey = birth_year + p["start_age"], birth_year + p["end_age"]
    return f"""
    <div style="border:{border};border-radius:12px;overflow:hidden;text-align:center;
                background:#fff;flex:0 0 auto;min-width:78px">
      <div style="font-size:9px;color:{ltx};background:{lbg};padding:4px 2px">
        {p['start_age']}–{p['end_age']}{'  ★' if is_active else ''}</div>
      <div style="padding:10px 4px 6px">
        <div style="font-size:26px;line-height:1;margin-bottom:2px">{STEMS[si]}</div>
        <div style="font-size:9px;color:#888">{STEMS_EN[si]}</div>
        <span style="font-size:9px;padding:1px 6px;border-radius:8px;
                     background:{c['bg']};color:{c['tx']}">{STEMS_EL[si]}</span>
      </div>
      <div style="border-top:0.5px solid #eee;padding:8px 4px 10px;background:#f8f7f4">
        <div style="font-size:20px;line-height:1;margin-bottom:3px">{BRANCHES[bi]}</div>
        <div style="font-size:10px;font-weight:500">{ANIMALS[bi]}</div>
        <div style="font-size:9px;color:#aaa;margin-top:2px">{sy}–{ey}</div>
      </div>
    </div>"""


def elem_balance_html(ec):
    max_e = max(ec.values()) or 1
    cards = "".join(
        f'<div style="background:{ECOL[el]["bg"]};border-radius:8px;padding:8px 4px;'
        f'text-align:center;flex:1">'
        f'<div style="font-size:10px;font-weight:500;color:{ECOL[el]["tx"]};margin-bottom:3px">{el}</div>'
        f'<div style="font-size:18px;font-weight:500;color:{ECOL[el]["bar"]}">{ec[el]}</div>'
        f'<div style="height:3px;border-radius:2px;background:#ddd;margin:5px 6px 0">'
        f'<div style="height:3px;border-radius:2px;background:{ECOL[el]["bar"]};'
        f'width:{round(ec[el]/max_e*100)}%"></div></div></div>'
        for el in ["Wood","Fire","Earth","Metal","Water"]
    )
    return f'<div style="display:flex;gap:8px">{cards}</div>'


def chart_text(chart, year, month, day, hour, minute, gender, da_yun, stars):
    """Compact text summary used in prompts and export."""
    ys,yb = chart["year"]; ms,mb = chart["month"]
    ds,db = chart["day"];  hs,hb = chart["hour"]
    ec = chart["elements"]
    dy = da_yun
    lines = [
        f"Birth: {year}-{month:02d}-{day:02d} {hour:02d}:{minute:02d} UTC+8 | Gender: {gender}",
        "",
        "FOUR PILLARS",
        f"Hour   : {STEMS_EN[hs]} {STEMS[hs]} ({STEMS_EL[hs]}) / {BR_EN[hb]} {BRANCHES[hb]} ({BR_EL[hb]} {BR_POL[hb]}) {ANIMALS[hb]}",
        f"Day ★  : {STEMS_EN[ds]} {STEMS[ds]} ({STEMS_EL[ds]}) / {BR_EN[db]} {BRANCHES[db]} ({BR_EL[db]} {BR_POL[db]}) {ANIMALS[db]}",
        f"Month  : {STEMS_EN[ms]} {STEMS[ms]} ({STEMS_EL[ms]}) / {BR_EN[mb]} {BRANCHES[mb]} ({BR_EL[mb]} {BR_POL[mb]}) {ANIMALS[mb]}",
        f"Year   : {STEMS_EN[ys]} {STEMS[ys]} ({STEMS_EL[ys]}) / {BR_EN[yb]} {BRANCHES[yb]} ({BR_EL[yb]} {BR_POL[yb]}) {ANIMALS[yb]}",
        "",
        f"Day Master: {STEMS_EL[ds]} ({STEMS[ds]}) — {DM_DESC.get(STEMS_EL[ds],'')}",
        "",
        f"Element Balance: Wood {ec['Wood']} | Fire {ec['Fire']} | Earth {ec['Earth']} | Metal {ec['Metal']} | Water {ec['Water']}",
        "",
        "DA YUN (10-year luck pillars):",
    ]
    for p in dy["pillars"]:
        lines.append(f"  Age {p['start_age']}-{p['end_age']}: {STEMS_EL[p['si']]} / {BR_EL[p['bi']]} {ANIMALS[p['bi']]}")
    if stars:
        lines.append("\nSPECIAL STARS: " + ", ".join(stars.keys()))
    return "\n".join(lines)


# ── Prompt builders ────────────────────────────────────────────────────────────
def build_natal_prompt(chart, year, month, day, hour, minute, gender, da_yun, stars):
    ctx = chart_text(chart, year, month, day, hour, minute, gender, da_yun, stars)
    active = next((p for p in da_yun["pillars"]
                   if p["start_age"] <= (_Date.today().year - year) <= p["end_age"]), None)
    active_str = ""
    if active:
        active_str = (f"\nCurrently in Da Yun: {STEMS_EL[active['si']]} / "
                      f"{BR_EL[active['bi']]} {ANIMALS[active['bi']]} "
                      f"(Age {active['start_age']}–{active['end_age']})")
    star_notes = "\n".join(f"- {k}: {STAR_DESC.get(k,'')}" for k in stars) if stars else "None detected."
    return f"""You are an expert BaZi (Four Pillars of Destiny) consultant. Analyse the chart and give a warm, specific, and actionable reading.

{ctx}{active_str}

Special Stars present:
{star_notes}

Provide seven sections:
1. **Character & Personality** — Day Master archetype and chart balance
2. **Strengths & Natural Talents** — what this person excels at
3. **Challenges & Growth Areas** — elemental gaps or tensions to navigate
4. **Career & Life Path** — suitable directions, industries, working styles
5. **Relationships & Love** — approach to partnerships, compatibility themes
6. **Health Tendencies** — areas to watch based on elemental imbalances
7. **Current Luck Period** — what the active Da Yun and current year bring

Use relatable modern language alongside Chinese metaphysical concepts. Be specific and avoid vague generalities.
"""


def build_forecast_prompt(chart, year, month, day, hour, minute, gender, da_yun):
    ctx = chart_text(chart, year, month, day, hour, minute, gender, da_yun, {})
    cy_pillar, cm_pillar = get_current_pillars()
    cy_si, cy_bi = cy_pillar
    cm_si, cm_bi = cm_pillar
    today = _Date.today()
    current_age = today.year - year
    active = next((p for p in da_yun["pillars"]
                   if p["start_age"] <= current_age <= p["end_age"]), da_yun["pillars"][0])
    return f"""You are a BaZi consultant specialising in annual and monthly forecasts.

{ctx}

CURRENT PERIOD CONTEXT
Today: {today.strftime('%B %d, %Y')} | Age: {current_age}
Current Solar Year Pillar: {STEMS_EL[cy_si]} ({STEMS[cy_si]}) / {BR_EL[cy_bi]} {ANIMALS[cy_bi]}
Current Month Pillar: {STEMS_EL[cm_si]} ({STEMS[cm_si]}) / {BR_EL[cm_bi]} {ANIMALS[cm_bi]}
Active Da Yun: {STEMS_EL[active['si']]} / {BR_EL[active['bi']]} {ANIMALS[active['bi']]} (Age {active['start_age']}–{active['end_age']})

Please provide:
1. **Overall {today.year} Theme** — how the year pillar interacts with the natal chart and Da Yun
2. **Key Opportunities in {today.year}** — 2-3 specific areas to focus on
3. **Cautions for {today.year}** — energies to be mindful of
4. **Monthly Snapshot (remaining months of {today.year})** — one paragraph per month from {today.strftime('%B')} through December, covering the dominant energy and suggested focus

Be specific and practical. Name the relevant pillars when explaining interactions.
"""


def build_compat_prompt(chart1, y1, m1, d1, h1, mi1, g1,
                        chart2, y2, m2, d2, h2, mi2, g2):
    c1 = chart_text(chart1, y1, m1, d1, h1, mi1, g1, {"pillars":[],"start_years":0,"start_months":0,"forward":True}, {})
    c2 = chart_text(chart2, y2, m2, d2, h2, mi2, g2, {"pillars":[],"start_years":0,"start_months":0,"forward":True}, {})
    dm1 = STEMS_EL[chart1["day"][0]]
    dm2 = STEMS_EL[chart2["day"][0]]
    return f"""You are a BaZi compatibility consultant. Analyse the two charts below and provide a detailed compatibility reading.

=== PERSON 1 ({g1}) — Day Master: {dm1} ===
{c1}

=== PERSON 2 ({g2}) — Day Master: {dm2} ===
{c2}

Provide:
1. **Overall Compatibility Score** — rate 1–10 with explanation
2. **Natural Synergies** — where these two charts complement and support each other
3. **Friction Points** — clashing elements or branches to be aware of
4. **Romantic / Partnership Dynamics** — how they relate in close relationships
5. **Career & Financial Compatibility** — can they build together effectively?
6. **Advice for Both** — practical tips to bring out the best in this pairing

Be honest, balanced, and specific. Reference the actual pillar interactions.
"""


def build_chat_context(chart, da_yun, year, month, day, hour, minute, gender, stars,
                        reading=None, forecast=None, compat_reading=None):
    ctx = chart_text(chart, year, month, day, hour, minute, gender, da_yun, stars)
    extras = []
    if reading:
        extras.append(f"=== NATAL READING (already generated) ===\n{reading}")
    if forecast:
        extras.append(f"=== ANNUAL FORECAST (already generated) ===\n{forecast}")
    if compat_reading:
        extras.append(f"=== COMPATIBILITY READING (already generated) ===\n{compat_reading}")
    extra_block = ("\n\n" + "\n\n".join(extras)) if extras else ""
    has_readings = bool(extras)
    return (
        f"You are a knowledgeable and warm BaZi consultant. "
        f"You have access to the user's full chart"
        f"{' and all AI readings generated so far' if has_readings else ''}. "
        f"Answer questions with specific references to their pillars and readings.\n\n"
        f"{ctx}{extra_block}\n\n"
        f"Use all of the above context when answering."
    )


def generate_html_export(chart, da_yun, stars, year, month, day, hour, minute, gender,
                          reading=None, forecast=None, compat_reading=None, chat_display=None):
    import re
    from datetime import date

    def md_to_html(text):
        if not text:
            return ""
        text = re.sub(r'^#### (.+)$', r'<h4 style="font-size:13px;font-weight:600;margin:1rem 0 .4rem">\1</h4>', text, flags=re.MULTILINE)
        text = re.sub(r'^### (.+)$',  r'<h3 style="font-size:14px;font-weight:600;margin:1rem 0 .5rem">\1</h3>', text, flags=re.MULTILINE)
        text = re.sub(r'^## (.+)$',   r'<h2 style="font-size:16px;font-weight:600;margin:1.2rem 0 .6rem">\1</h2>', text, flags=re.MULTILINE)
        text = re.sub(r'\*\*\*(.+?)\*\*\*', r'<strong><em>\1</em></strong>', text)
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        paragraphs = re.split(r'\n{2,}', text)
        out = []
        for p in paragraphs:
            p = p.strip()
            if not p:
                continue
            if p.startswith('<h') or p.startswith('<ul') or p.startswith('<ol'):
                out.append(p)
            else:
                out.append(f'<p style="margin-bottom:.7rem;line-height:1.7">{p.replace(chr(10), "<br>")}</p>')
        return "\n".join(out)

    ys,yb = chart["year"]; ms,mb = chart["month"]
    ds,db = chart["day"];  hs,hb = chart["hour"]
    ec    = chart["elements"]
    dm_name = STEMS_EL[ds]
    current_age = date.today().year - year

    def export_pillar(label, si, bi, is_dm=False):
        c  = ECOL[stem_elem(si)]
        border = "2px solid #378ADD" if is_dm else "0.5px solid #ddd"
        lbg = "#E6F1FB" if is_dm else "#f4f3f0"
        ltx = "#185FA5" if is_dm else "#999"
        tag = " · Day Master" if is_dm else ""
        hs_items = "".join(
            f'<span style="font-size:9px;padding:1px 5px;border-radius:6px;margin:1px;'
            f'background:{ECOL[stem_elem(idx)]["bg"]};color:{ECOL[stem_elem(idx)]["tx"]}">'
            f'{STEMS[idx]} {w}</span>'
            for idx, w in get_hidden_stems(bi)
        )
        return (
            f'<div style="flex:1;border:{border};border-radius:12px;overflow:hidden;text-align:center;background:#fff">'
            f'<div style="font-size:10px;color:{ltx};background:{lbg};padding:5px 0;letter-spacing:.04em">{label}{tag}</div>'
            f'<div style="padding:14px 6px 8px">'
            f'<div style="font-size:30px;line-height:1;margin-bottom:3px">{STEMS[si]}</div>'
            f'<div style="font-size:11px;color:#888;margin-bottom:4px">{STEMS_EN[si]}</div>'
            f'<span style="font-size:10px;font-weight:500;padding:2px 8px;border-radius:12px;background:{c["bg"]};color:{c["tx"]}">{STEMS_EL[si]}</span>'
            f'</div>'
            f'<div style="border-top:0.5px solid #eee;padding:8px 6px 8px;background:#f8f7f4">'
            f'<div style="font-size:24px;line-height:1;margin-bottom:3px">{BRANCHES[bi]}</div>'
            f'<div style="font-size:12px;font-weight:500">{ANIMALS[bi]}</div>'
            f'<div style="font-size:10px;color:#888;margin-top:2px">{BR_EL[bi]} · {BR_POL[bi]}</div>'
            f'<div style="margin-top:5px;display:flex;flex-wrap:wrap;justify-content:center;gap:2px">{hs_items}</div>'
            f'</div></div>'
        )

    pillars_html = (
        f'<div style="display:flex;gap:10px;margin-bottom:1.2rem">'
        f'{export_pillar("Hour 时",hs,hb)}'
        f'{export_pillar("Day 日",ds,db,True)}'
        f'{export_pillar("Month 月",ms,mb)}'
        f'{export_pillar("Year 年",ys,yb)}'
        f'</div>'
    )

    max_e = max(ec.values()) or 1
    elem_html = '<div style="display:flex;gap:8px;margin-bottom:1.5rem">' + "".join(
        f'<div style="flex:1;background:{ECOL[el]["bg"]};border-radius:8px;padding:8px 4px;text-align:center">'
        f'<div style="font-size:10px;font-weight:500;color:{ECOL[el]["tx"]};margin-bottom:3px">{el}</div>'
        f'<div style="font-size:18px;font-weight:500;color:{ECOL[el]["bar"]}">{ec[el]}</div>'
        f'<div style="height:3px;border-radius:2px;background:#ddd;margin:5px 6px 0">'
        f'<div style="height:3px;border-radius:2px;background:{ECOL[el]["bar"]};width:{round(ec[el]/max_e*100)}%"></div></div></div>'
        for el in ["Wood","Fire","Earth","Metal","Water"]
    ) + '</div>'

    stars_html = ""
    if stars:
        cards = "".join(
            f'<div style="border:0.5px solid #ddd;border-radius:10px;padding:10px 14px;margin-bottom:8px;background:#fff">'
            f'<span style="font-size:13px;font-weight:600">{name}</span>'
            f'<span style="font-size:11px;color:#888;margin-left:8px">in {branch}</span>'
            f'<div style="font-size:12px;color:#555;margin-top:3px">{STAR_DESC.get(name,"")}</div></div>'
            for name, branch in stars.items()
        )
        stars_html = f'<h3 style="font-size:14px;font-weight:600;margin:1rem 0 .6rem">Special Stars</h3>{cards}'

    dy_cards = "".join(
        (lambda p, active: (
            f'<div style="flex:0 0 auto;min-width:78px;border:{"2px solid #378ADD" if active else "0.5px solid #ddd"};'
            f'border-radius:12px;overflow:hidden;text-align:center;background:#fff">'
            f'<div style="font-size:9px;color:{"#185FA5" if active else "#999"};'
            f'background:{"#E6F1FB" if active else "#f4f3f0"};padding:4px 2px">'
            f'{p["start_age"]}–{p["end_age"]}{"  ★" if active else ""}</div>'
            f'<div style="padding:8px 4px 6px">'
            f'<div style="font-size:22px;line-height:1;margin-bottom:2px">{STEMS[p["si"]]}</div>'
            f'<div style="font-size:9px;color:#888;margin-bottom:3px">{STEMS_EN[p["si"]]}</div>'
            f'<span style="font-size:9px;padding:1px 6px;border-radius:8px;'
            f'background:{ECOL[stem_elem(p["si"])]["bg"]};color:{ECOL[stem_elem(p["si"])]["tx"]}">'
            f'{STEMS_EL[p["si"]]}</span></div>'
            f'<div style="border-top:0.5px solid #eee;padding:6px 4px 8px;background:#f8f7f4">'
            f'<div style="font-size:18px;line-height:1;margin-bottom:2px">{BRANCHES[p["bi"]]}</div>'
            f'<div style="font-size:9px;font-weight:500">{ANIMALS[p["bi"]]}</div>'
            f'<div style="font-size:9px;color:#aaa;margin-top:2px">{year+p["start_age"]}–{year+p["end_age"]}</div>'
            f'</div></div>'
        ))(p, p["start_age"] <= current_age <= p["end_age"])
        for p in da_yun["pillars"]
    )
    dy_html = (
        f'<h3 style="font-size:14px;font-weight:600;margin:1rem 0 .4rem">10-Year Luck Pillars 大运</h3>'
        f'<p style="font-size:11px;color:#888;margin-bottom:8px">'
        f'Direction: {"forward" if da_yun["forward"] else "backward"} &nbsp;·&nbsp; '
        f'First pillar at age {da_yun["start_years"]} yrs {da_yun["start_months"]} mo</p>'
        f'<div style="display:flex;gap:8px;overflow-x:auto;padding-bottom:8px;margin-bottom:1.5rem">{dy_cards}</div>'
    )

    def ai_section(title, content):
        if not content:
            return ""
        return (
            f'<hr style="border:none;border-top:0.5px solid #e0dedd;margin:1.8rem 0">'
            f'<h2 style="font-size:18px;font-weight:600;margin-bottom:1rem">{title}</h2>'
            f'<div style="font-size:13px;color:#333">{md_to_html(content)}</div>'
        )

    chat_html = ""
    visible = [m for m in (chat_display or []) if not (m["role"] == "assistant" and "reviewed your full BaZi chart" in m["content"] and len(m["content"]) < 200)]
    if visible:
        msgs = "".join(
            f'<div style="margin-bottom:10px;padding:10px 14px;border-radius:10px;font-size:13px;line-height:1.6;'
            f'{"background:#f0eeeb" if m["role"]=="user" else "background:#fff;border:0.5px solid #ddd"}">'
            f'<div style="font-size:10px;color:#888;margin-bottom:4px;font-weight:500;letter-spacing:.05em">'
            f'{"YOU" if m["role"]=="user" else "CONSULTANT"}</div>'
            f'{m["content"]}</div>'
            for m in visible
        )
        chat_html = (
            f'<hr style="border:none;border-top:0.5px solid #e0dedd;margin:1.8rem 0">'
            f'<h2 style="font-size:18px;font-weight:600;margin-bottom:1rem">Chat History</h2>'
            f'{msgs}'
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>BaZi Reading — {year}/{month:02d}/{day:02d}</title>
<style>
  *{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:system-ui,-apple-system,sans-serif;background:#f8f7f4;color:#1a1a18;padding:2rem}}
  .wrap{{max-width:800px;margin:0 auto}}
  @media print{{body{{background:#fff;padding:0}} .pillars,.dayun{{page-break-inside:avoid}}}}
</style>
</head>
<body><div class="wrap">
  <h1 style="font-size:22px;font-weight:600;margin-bottom:4px">BaZi Reading 八字</h1>
  <p style="color:#888;font-size:13px;margin-bottom:1.2rem">AI-powered Four Pillars of Destiny analysis</p>
  <div style="background:#fff;border:0.5px solid #ddd;border-radius:12px;padding:12px 16px;margin-bottom:1.5rem;font-size:13px;color:#555">
    <strong>Birth:</strong> {year}/{month:02d}/{day:02d} &nbsp;·&nbsp; {hour:02d}:{minute:02d} UTC+8 &nbsp;·&nbsp;
    {gender} &nbsp;·&nbsp; Age {current_age} &nbsp;·&nbsp; Day Master: {dm_name}
  </div>
  <div style="font-size:11px;color:#888;margin-bottom:8px">Four Pillars — Hour · Day · Month · Year (hidden stems shown in branch)</div>
  {pillars_html}
  <div style="border:0.5px solid #ddd;border-radius:12px;padding:14px 16px;margin-bottom:1rem;background:#fff">
    <div style="font-size:11px;color:#888;margin-bottom:5px">Day Master 日主</div>
    <div style="font-size:15px;font-weight:600;margin-bottom:4px">{STEMS[ds]}{BRANCHES[db]} · {dm_name}</div>
    <div style="font-size:12px;color:#666">{DM_DESC.get(dm_name,"")}</div>
  </div>
  <div style="font-size:11px;color:#888;margin-bottom:6px">Element Balance (stems + branch main qi)</div>
  {elem_html}
  {stars_html}
  {dy_html}
  {ai_section("Natal Reading", reading)}
  {ai_section(f"{date.today().year} Annual Forecast", forecast)}
  {ai_section("Compatibility Reading", compat_reading)}
  {chat_html}
  <div style="font-size:11px;color:#999;text-align:center;margin-top:2rem;padding-top:1rem;border-top:0.5px solid #eee">
    Generated by BaZi Reader 八字 &nbsp;·&nbsp; {date.today().strftime("%B %d, %Y")} &nbsp;·&nbsp; For reference purposes only
  </div>
</div></body></html>"""


# ── URL param helpers ─────────────────────────────────────────────────────────
def _pi(k, d):
    try: return int(st.query_params[k])
    except: return d

def _ps(k, d):
    try: return str(st.query_params[k])
    except: return d


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("<h1 style='font-size:22px;font-weight:600;margin-bottom:2px'>BaZi Reader 八字</h1>",
            unsafe_allow_html=True)
st.markdown("<p style='color:#888;font-size:13px;margin-bottom:1.2rem'>AI-powered Four Pillars of Destiny analysis</p>",
            unsafe_allow_html=True)

# ── Input form ────────────────────────────────────────────────────────────────
with st.form("bazi_form"):
    c1, c2, c3 = st.columns(3)
    year   = c1.number_input("Year",        min_value=1900, max_value=2100, value=_pi("yr", 2004))
    month  = c2.number_input("Month",       min_value=1,    max_value=12,   value=_pi("mo", 12))
    day    = c3.number_input("Day",         min_value=1,    max_value=31,   value=_pi("dy", 2))
    c4, c5, c6 = st.columns(3)
    hour   = c4.number_input("Hour (0–23)", min_value=0,    max_value=23,   value=_pi("hr", 9))
    minute = c5.number_input("Minute",      min_value=0,    max_value=59,   value=_pi("mn", 31))
    gender = c6.selectbox("Gender", ["Female","Male"],
                          index=1 if _ps("gd","F") == "M" else 0)
    st.caption("UTC+8 — Singapore / HK / China / Malaysia. No longitude correction.")
    submitted = st.form_submit_button("Calculate & Analyse →", use_container_width=True)

if submitted:
    new_info = (int(year), int(month), int(day), int(hour), int(minute), gender)
    if ss.birth_info != new_info:
        ss.reading = None
        ss.forecast = None
        ss.compat_reading = None
        ss.chat_display = []
        ss.chat_history = []
        ss.birth_info = new_info
        ss.chart  = calculate_bazi(*new_info[:5])
        ss.da_yun = calculate_da_yun(*new_info[:5], new_info[5])
        ss.stars  = get_special_stars(ss.chart)
    ss.form_submitted = True
    st.query_params.update({"yr":int(year),"mo":int(month),"dy":int(day),
                            "hr":int(hour),"mn":int(minute),"gd":gender[0]})

if not ss.form_submitted:
    st.stop()

# ── Unpack session state ───────────────────────────────────────────────────────
year, month, day, hour, minute, gender = ss.birth_info
chart  = ss.chart
da_yun = ss.da_yun
stars  = ss.stars
ys,yb  = chart["year"]; ms,mb = chart["month"]
ds,db  = chart["day"];  hs,hb = chart["hour"]
ec     = chart["elements"]
dm_name = STEMS_EL[ds]

current_age = _Date.today().year - year

st.markdown("---")

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Chart", "Luck Pillars", "AI Insights", "Compatibility", "Chat"]
)

# ═══════════════════════════════════════════════════════════════════
# TAB 1 — CHART
# ═══════════════════════════════════════════════════════════════════
with tab1:
    st.markdown("<div style='font-size:11px;color:#888;margin-bottom:8px'>Four Pillars — Hour · Day · Month · Year (hidden stems shown in each branch)</div>",
                unsafe_allow_html=True)
    st.markdown(
        f'<div style="display:flex;gap:10px;margin-bottom:1.2rem">'
        f'{pillar_card("Hour 时", hs, hb)}'
        f'{pillar_card("Day 日",  ds, db, is_dm=True)}'
        f'{pillar_card("Month 月", ms, mb)}'
        f'{pillar_card("Year 年",  ys, yb)}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # Day master box
    st.markdown(f"""
    <div style="border:0.5px solid #ddd;border-radius:12px;padding:.9rem 1.1rem;
                margin-bottom:1rem;background:#fff">
      <div style="font-size:11px;color:#888;margin-bottom:5px">Day Master 日主</div>
      <div style="font-size:15px;font-weight:600">{STEMS[ds]}{BRANCHES[db]} · {dm_name}</div>
      <div style="font-size:12px;color:#666;margin-top:4px">{DM_DESC.get(dm_name,'')}</div>
    </div>""", unsafe_allow_html=True)

    # Element balance
    st.markdown("<div style='font-size:11px;color:#888;margin-bottom:6px'>Element Balance (stems + branch main qi)</div>",
                unsafe_allow_html=True)
    st.markdown(f'<div style="margin-bottom:1.2rem">{elem_balance_html(ec)}</div>',
                unsafe_allow_html=True)

    # Special stars
    if stars:
        st.markdown("**Special Stars detected in your chart**")
        for name, branch_name in stars.items():
            desc = STAR_DESC.get(name, "")
            st.markdown(
                f'<div style="border:0.5px solid #ddd;border-radius:10px;padding:.7rem 1rem;'
                f'margin-bottom:.5rem;background:#fff">'
                f'<span style="font-size:13px;font-weight:600">{name}</span>'
                f'<span style="font-size:11px;color:#888;margin-left:8px">in {branch_name}</span>'
                f'<div style="font-size:12px;color:#555;margin-top:3px">{desc}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("No major special stars detected in the natal branches.")

    # Share link
    st.markdown("---")
    col_share, col_export = st.columns(2)
    with col_share:
        if st.button("Copy share link", use_container_width=True):
            st.info("URL updated — copy it from your browser's address bar.")
    with col_export:
        html_data = generate_html_export(
            chart, da_yun, stars, year, month, day, hour, minute, gender,
            reading=ss.reading, forecast=ss.forecast,
            compat_reading=ss.compat_reading, chat_display=ss.chat_display,
        )
        st.download_button("Export full report (.html)", data=html_data,
                           file_name=f"bazi_{year}{month:02d}{day:02d}.html",
                           mime="text/html", use_container_width=True)

# ═══════════════════════════════════════════════════════════════════
# TAB 2 — LUCK PILLARS
# ═══════════════════════════════════════════════════════════════════
with tab2:
    sy = da_yun["start_years"]
    sm = da_yun["start_months"]
    direction = "forward (顺行)" if da_yun["forward"] else "backward (逆行)"
    st.markdown(
        f"First luck pillar begins at age **{sy}** years {sm} months &nbsp;·&nbsp; "
        f"Direction: **{direction}**",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='font-size:11px;color:#888;margin:10px 0 6px'>Scroll right to see all pillars — current period marked ★</div>",
                unsafe_allow_html=True)

    cards_html = "".join(
        da_yun_card(p, year, p["start_age"] <= current_age <= p["end_age"])
        for p in da_yun["pillars"]
    )
    st.markdown(
        f'<div style="display:flex;gap:8px;overflow-x:auto;padding-bottom:8px">{cards_html}</div>',
        unsafe_allow_html=True,
    )

    # Active pillar detail
    active = next((p for p in da_yun["pillars"]
                   if p["start_age"] <= current_age <= p["end_age"]), None)
    if active:
        asi, abi = active["si"], active["bi"]
        c = ECOL[stem_elem(asi)]
        st.markdown(
            f'<div style="border:0.5px solid #ddd;border-radius:12px;padding:.9rem 1.1rem;'
            f'margin-top:1rem;background:#fff">'
            f'<div style="font-size:11px;color:#888;margin-bottom:5px">Currently active luck pillar (age {active["start_age"]}–{active["end_age"]})</div>'
            f'<div style="font-size:15px;font-weight:600">{STEMS[asi]}{BRANCHES[abi]} · '
            f'<span style="background:{c["bg"]};color:{c["tx"]};padding:2px 8px;'
            f'border-radius:8px;font-size:13px">{STEMS_EL[asi]}</span></div>'
            f'<div style="font-size:12px;color:#666;margin-top:4px">'
            f'{BR_EL[abi]} {BR_POL[abi]} {ANIMALS[abi]} branch</div>'
            f'</div>',
            unsafe_allow_html=True,
        )

# ═══════════════════════════════════════════════════════════════════
# TAB 3 — AI INSIGHTS
# ═══════════════════════════════════════════════════════════════════
with tab3:
    api_key = get_api_key()
    if not api_key:
        st.warning("Add `GEMINI_API_KEY` to `.env` (local) or Streamlit secrets (cloud) to enable AI features.")
        st.stop()

    # Natal reading
    st.markdown("#### Natal Reading")
    if ss.reading is None:
        if st.button("Generate natal reading", use_container_width=True):
            with st.spinner("Consulting the stars..."):
                try:
                    prompt = build_natal_prompt(chart, year, month, day, hour, minute,
                                                gender, da_yun, stars)
                    resp = gemini_model().generate_content(prompt)
                    ss.reading = resp.text
                    ss.chat_history = []; ss.chat_display = []
                except Exception as e:
                    st.error(f"Gemini error: {e}")
    if ss.reading:
        st.markdown(ss.reading)
        if st.button("Regenerate natal reading"):
            ss.reading = None
            st.rerun()

    st.markdown("---")

    # Forecast
    st.markdown(f"#### {_Date.today().year} Forecast")
    if ss.forecast is None:
        if st.button("Generate annual forecast", use_container_width=True):
            with st.spinner("Mapping the year ahead..."):
                try:
                    prompt = build_forecast_prompt(chart, year, month, day, hour, minute,
                                                   gender, da_yun)
                    resp = gemini_model().generate_content(prompt)
                    ss.forecast = resp.text
                    ss.chat_history = []; ss.chat_display = []
                except Exception as e:
                    st.error(f"Gemini error: {e}")
    if ss.forecast:
        st.markdown(ss.forecast)
        if st.button("Regenerate forecast"):
            ss.forecast = None
            st.rerun()

# ═══════════════════════════════════════════════════════════════════
# TAB 4 — COMPATIBILITY
# ═══════════════════════════════════════════════════════════════════
with tab4:
    st.markdown("Enter a second person's birth details to compare charts.")
    with st.form("compat_form"):
        cc1, cc2, cc3 = st.columns(3)
        cy2 = cc1.number_input("Year",        min_value=1900, max_value=2100, value=1995, key="cy2")
        cm2 = cc2.number_input("Month",       min_value=1,    max_value=12,   value=6,    key="cm2")
        cd2 = cc3.number_input("Day",         min_value=1,    max_value=31,   value=15,   key="cd2")
        cc4, cc5, cc6 = st.columns(3)
        ch2 = cc4.number_input("Hour (0–23)", min_value=0,    max_value=23,   value=8,    key="ch2")
        cmi2 = cc5.number_input("Minute",     min_value=0,    max_value=59,   value=0,    key="cmi2")
        cg2 = cc6.selectbox("Gender", ["Male","Female"], key="cg2")
        compat_submitted = st.form_submit_button("Compare Charts →", use_container_width=True)

    if compat_submitted:
        with st.spinner("Comparing charts..."):
            try:
                chart2 = calculate_bazi(int(cy2), int(cm2), int(cd2), int(ch2), int(cmi2))
                prompt = build_compat_prompt(
                    chart,  year,    month,    day,    hour,    minute,    gender,
                    chart2, int(cy2), int(cm2), int(cd2), int(ch2), int(cmi2), cg2,
                )
                resp = gemini_model().generate_content(prompt)
                ss.compat_reading = resp.text
                ss.chat_history = []; ss.chat_display = []
            except Exception as e:
                st.error(f"Gemini error: {e}")

    if ss.compat_reading:
        st.markdown(ss.compat_reading)

# ═══════════════════════════════════════════════════════════════════
# TAB 5 — CHAT
# ═══════════════════════════════════════════════════════════════════
with tab5:
    st.markdown("Ask me anything about your BaZi chart.")

    # Build or rebuild chat context (includes any readings generated so far)
    if not ss.chat_history:
        ctx_msg = build_chat_context(
            chart, da_yun, year, month, day, hour, minute, gender, stars,
            reading=ss.reading, forecast=ss.forecast, compat_reading=ss.compat_reading,
        )
        has = [x for x in ["natal reading", "annual forecast", "compatibility reading"]
               if [ss.reading, ss.forecast, ss.compat_reading][["natal reading","annual forecast","compatibility reading"].index(x)]]
        context_note = (f"Context loaded: chart + {', '.join(has)}." if has
                        else "Context loaded: chart only. Generate readings in the AI Insights tab to give me more to work with.")
        intro = f"I've reviewed your full BaZi chart{' and your ' + ', '.join(has) if has else ''}. Ask me anything — your personality, current luck pillar, relationships, health, career, or what this year holds for you."
        ss.chat_history = [
            {"role": "user",  "parts": [ctx_msg]},
            {"role": "model", "parts": [intro]},
        ]
        ss.chat_display = [
            {"role": "assistant", "content": intro},
        ]
        st.caption(context_note)

    for msg in ss.chat_display:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Ask about your chart...")
    if user_input:
        ss.chat_display.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        with st.chat_message("assistant"):
            with st.spinner(""):
                try:
                    chat_session = gemini_model().start_chat(history=ss.chat_history)
                    resp = chat_session.send_message(user_input)
                    answer = resp.text
                    ss.chat_history.append({"role": "user",  "parts": [user_input]})
                    ss.chat_history.append({"role": "model", "parts": [answer]})
                    ss.chat_display.append({"role": "assistant", "content": answer})
                    st.markdown(answer)
                except Exception as e:
                    st.error(f"Gemini error: {e}")

st.markdown(
    "<div style='font-size:11px;color:#999;margin-top:1.5rem;text-align:center'>"
    "Formula: advanced fractional solar-term model · UTC+8 only · For reference purposes</div>",
    unsafe_allow_html=True,
)
