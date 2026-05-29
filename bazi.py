from datetime import date as _Date

__version__ = "2.0.0"

STEMS    = ["甲","乙","丙","丁","戊","己","庚","辛","壬","癸"]
STEMS_EN = ["Jiǎ","Yǐ","Bǐng","Dīng","Wù","Jǐ","Gēng","Xīn","Rén","Guǐ"]
STEMS_EL = ["Yang Wood","Yin Wood","Yang Fire","Yin Fire","Yang Earth",
            "Yin Earth","Yang Metal","Yin Metal","Yang Water","Yin Water"]

BRANCHES = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
BR_EN    = ["Zǐ","Chǒu","Yín","Mǎo","Chén","Sì","Wǔ","Wèi","Shēn","Yǒu","Xū","Hài"]
ANIMALS  = ["Rat","Ox","Tiger","Rabbit","Dragon","Snake","Horse",
            "Goat","Monkey","Rooster","Dog","Pig"]
BR_EL    = ["Water","Earth","Wood","Wood","Earth","Fire","Fire",
            "Earth","Metal","Metal","Earth","Water"]
BR_POL   = ["Yang","Yin","Yang","Yin","Yang","Yin","Yang","Yin","Yang","Yin","Yang","Yin"]

TERM_MONTHS   = [2,3,4,5,6,7,8,9,10,11,12,1]
TERM_BRANCHES = [2,3,4,5,6,7,8,9,10,11,0,1]
ZODIAC_MONTH_NUM = {2:3,3:4,4:5,5:6,6:7,7:8,8:9,9:10,10:11,11:12,0:1,1:2}

# Hidden stems (藏干) per branch — list of (stem_index, weight)
HIDDEN_STEMS = [
    [(8,"main")],                                    # 子 Rat
    [(5,"main"),(9,"mid"),(7,"minor")],              # 丑 Ox
    [(0,"main"),(2,"mid"),(4,"minor")],              # 寅 Tiger
    [(1,"main")],                                    # 卯 Rabbit
    [(4,"main"),(1,"mid"),(9,"minor")],              # 辰 Dragon
    [(2,"main"),(6,"mid"),(4,"minor")],              # 巳 Snake
    [(3,"main"),(5,"mid")],                          # 午 Horse
    [(5,"main"),(3,"mid"),(1,"minor")],              # 未 Goat
    [(6,"main"),(8,"mid"),(4,"minor")],              # 申 Monkey
    [(7,"main")],                                    # 酉 Rooster
    [(4,"main"),(7,"mid"),(3,"minor")],              # 戌 Dog
    [(8,"main"),(0,"mid")],                          # 亥 Pig
]

# Special star lookup tables
NOBLEMAN         = {0:[1,7],1:[0,8],2:[11,9],3:[11,9],4:[1,7],
                    5:[0,8],6:[1,7],7:[6,2],8:[3,5],9:[3,5]}
PEACH_BLOSSOM    = {0:9,1:6,2:3,3:0,4:9,5:6,6:3,7:0,8:9,9:6,10:3,11:0}
ACADEMIC_STAR    = [5,6,8,9,8,9,11,0,2,3]   # indexed by day stem
TRAVELLING_HORSE = {0:2,1:11,2:8,3:5,4:2,5:11,6:8,7:5,8:2,9:11,10:8,11:5}
CANOPY_STAR      = {0:4,1:1,2:10,3:7,4:4,5:1,6:10,7:7,8:4,9:1,10:10,11:7}


def get_term_float(year, ti):
    c20 = [4.6295,5.59,5.59,6.318,6.5,7.928,8.35,8.44,9.098,8.218,7.9,6.11]
    c21 = [3.87,5.63,4.81,5.52,5.678,7.108,7.5,7.646,8.318,7.438,7.18,5.4055]
    c = c20[ti] if year <= 2000 else c21[ti]
    y = year % 100
    return (y * 0.2422 + c) - (y // 4)


def get_month_branch(year, month, day, hour, minute):
    branch = 1
    comp_month = 13 if month == 1 else month
    user_day_float = day + (hour / 24) + (minute / 1440)
    for i in range(12):
        tm = 13 if TERM_MONTHS[i] == 1 else TERM_MONTHS[i]
        if comp_month > tm or (comp_month == tm and user_day_float >= get_term_float(year, i)):
            branch = TERM_BRANCHES[i]
    return branch


def is_leap(y):
    return (y % 4 == 0 and y % 100 != 0) or y % 400 == 0


def day_of_year(y, m, d):
    md = [0,31,28,31,30,31,30,31,31,30,31,30,31]
    if is_leap(y):
        md[2] = 29
    return sum(md[1:m]) + d


def get_day_pillar(y, m, d):
    total = (y - 1900) * 365 + (y - 1901) // 4 + day_of_year(y, m, d)
    idx = (total + 10) % 60
    si = 9 if idx % 10 == 0 else (idx % 10) - 1
    bi = 11 if idx % 12 == 0 else (idx % 12) - 1
    return si, bi


def get_hour_branch(h):
    if h == 0:  return 0
    if h <= 2:  return 1
    if h <= 4:  return 2
    if h <= 6:  return 3
    if h <= 8:  return 4
    if h <= 10: return 5
    if h <= 12: return 6
    if h <= 14: return 7
    if h <= 16: return 8
    if h <= 18: return 9
    if h <= 20: return 10
    if h <= 22: return 11
    return 0


def get_hour_stem(dsi1, hbi1, late_rat):
    raw = (dsi1 * 2 - 1) + (hbi1 - 1) + (12 if late_rat else 0)
    s = raw % 10
    if s == 0:
        s = 10
    return s - 1


def stem_elem(i):
    return ["Wood","Wood","Fire","Fire","Earth","Earth","Metal","Metal","Water","Water"][i]


def branch_elem(i):
    return BR_EL[i]


def calculate_bazi(year, month, day, hour, minute):
    user_day_float = day + (hour / 24) + (minute / 1440)
    lichun_float = get_term_float(year, 0)

    ey = year
    if month < 2 or (month == 2 and user_day_float < lichun_float):
        ey = year - 1

    y_si = ((ey - 4) % 10 + 10) % 10
    y_bi = ((ey - 4) % 12 + 12) % 12

    m_bi = get_month_branch(year, month, day, hour, minute)
    zmn = ZODIAC_MONTH_NUM[m_bi]
    m_raw = (y_si + 1) * 2 - 1 + (zmn - 1)
    if zmn in (1, 2):
        m_raw += 12
    m_si = m_raw % 10
    if m_si == 0:
        m_si = 10
    m_si -= 1

    d_si, d_bi = get_day_pillar(year, month, day)
    h_bi = get_hour_branch(hour)
    h_si = get_hour_stem(d_si + 1, h_bi + 1, hour == 23)

    ec = {"Wood": 0, "Fire": 0, "Earth": 0, "Metal": 0, "Water": 0}
    for s in [y_si, m_si, d_si, h_si]:
        ec[stem_elem(s)] += 1
    for b in [y_bi, m_bi, d_bi, h_bi]:
        ec[branch_elem(b)] += 1

    return {
        "year":     (y_si, y_bi),
        "month":    (m_si, m_bi),
        "day":      (d_si, d_bi),
        "hour":     (h_si, h_bi),
        "elements": ec,
    }


def get_hidden_stems(bi):
    return HIDDEN_STEMS[bi]


def get_special_stars(chart):
    ds, db = chart["day"]
    _,  yb = chart["year"]
    _,  hb = chart["hour"]
    _,  mb = chart["month"]
    all_b  = {yb, mb, db, hb}
    stars  = {}

    found_nb = [b for b in all_b if b in NOBLEMAN.get(ds, [])]
    if found_nb:
        stars["Nobleman Star 天乙贵人"] = ", ".join(ANIMALS[b] for b in found_nb)

    pb = PEACH_BLOSSOM.get(db)
    if pb in all_b:
        stars["Peach Blossom 桃花"] = ANIMALS[pb]

    ac = ACADEMIC_STAR[ds]
    if ac in all_b:
        stars["Academic Star 文昌"] = ANIMALS[ac]

    th = TRAVELLING_HORSE.get(db)
    if th in all_b:
        stars["Travelling Horse 驿马"] = ANIMALS[th]

    ca = CANOPY_STAR.get(db)
    if ca in all_b:
        stars["Canopy Star 华盖"] = ANIMALS[ca]

    return stars


def calculate_da_yun(year, month, day, hour, minute, gender):
    chart = calculate_bazi(year, month, day, hour, minute)
    y_si, _ = chart["year"]
    m_si, m_bi = chart["month"]

    year_is_yang = (y_si % 2 == 0)
    forward = (gender == "Male" and year_is_yang) or \
              (gender == "Female" and not year_is_yang)

    birth = _Date(year, month, day)

    all_terms = []
    for y in range(year - 1, year + 3):
        for ti in range(12):
            tm = TERM_MONTHS[ti]
            td = max(1, int(get_term_float(y, ti)))
            try:
                all_terms.append(_Date(y, tm, min(td, 28)))
            except ValueError:
                pass
    all_terms.sort()

    before = [d for d in all_terms if d <= birth]
    after  = [d for d in all_terms if d > birth]
    if forward:
        days = (after[0] - birth).days if after else 0
    else:
        days = (birth - before[-1]).days if before else 0
    days = max(0, days)

    start_years  = days // 3
    start_months = (days % 3) * 4

    pillars = []
    for i in range(1, 9):
        si = (m_si + i) % 10 if forward else (m_si - i + 10) % 10
        bi = (m_bi + i) % 12 if forward else (m_bi - i + 12) % 12
        start_age = start_years + (i - 1) * 10
        pillars.append({"si": si, "bi": bi,
                        "start_age": start_age, "end_age": start_age + 9})

    return {"start_years": start_years, "start_months": start_months,
            "forward": forward, "pillars": pillars}


def get_current_pillars():
    """Return ((y_si,y_bi), (m_si,m_bi)) for today's solar year and month."""
    today = _Date.today()
    y, m, d = today.year, today.month, today.day
    lf = get_term_float(y, 0)
    cy = y if not (m < 2 or (m == 2 and d < int(lf))) else y - 1
    cy_si = ((cy - 4) % 10 + 10) % 10
    cy_bi = ((cy - 4) % 12 + 12) % 12
    m_bi  = get_month_branch(y, m, d, 12, 0)
    zmn   = ZODIAC_MONTH_NUM[m_bi]
    m_raw = (cy_si + 1) * 2 - 1 + (zmn - 1)
    if zmn in (1, 2):
        m_raw += 12
    m_si = m_raw % 10
    if m_si == 0:
        m_si = 10
    m_si -= 1
    return (cy_si, cy_bi), (m_si, m_bi)
