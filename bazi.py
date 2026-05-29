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
    return 0  # h=23, late rat


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
