#!/usr/bin/env python3
"""Build the static site in web/ from data/recipes.json (+ optional transcriptions).

Usage:  python3 tools/build.py
Stdlib only. Re-run after editing data/ — it rewrites every generated page.
"""
import html
import json
import re
import struct
import unicodedata
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
DATA = json.loads((ROOT / "data" / "recipes.json").read_text(encoding="utf-8"))
TRANS_DIR = ROOT / "data" / "transcriptions"
SITE = DATA["site"]
CATS = DATA["categories"]
CAT_SLUG = {c["name"]: c["slug"] for c in CATS}
RECIPES = [r for r in DATA["recipes"] if not r.get("hidden")]
TODAY = date.today().isoformat()
E = lambda s: html.escape(str(s), quote=True)

KOSHER_CLASS = {"בשרי": "k-meat", "פרווה": "k-parve", "חלבי": "k-dairy"}
TAG_CLASS = {"חגיגי": "t-festive"}


# ---------- helpers ----------
def jpeg_size(path):
    d = path.read_bytes()
    i = 2
    while i < len(d):
        if d[i] != 0xFF:
            i += 1
            continue
        marker = d[i + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", d[i + 5:i + 9])
            return w, h
        i += 2 + struct.unpack(">H", d[i + 2:i + 4])[0]
    return None


def norm(s):
    s = unicodedata.normalize("NFC", s or "").lower()
    s = re.sub(r"[֑-ׇ]", "", s)
    s = re.sub(r"[׳'`´’״\"]", "", s)
    s = re.sub(r"[-–—_.,:;!?()\[\]]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def load_transcription(rid):
    p = TRANS_DIR / f"{rid}.json"
    if not p.exists():
        return None
    return json.loads(p.read_text(encoding="utf-8"))


def mark_unsure(text):
    """Escape, then render word[?] and bare [?] as highlighted spans."""
    t = E(text)
    t = re.sub(r"(\S+?)\[\?\]",
               r'<span class="unsure" title="מילה לא ודאית">\1</span><span class="sr-only"> (לא ודאי)</span>', t)
    t = t.replace("[?]", '<span class="unsure" title="לא קריא">…</span><span class="sr-only">מילה לא קריאה</span>')
    return t


def badges(r):
    out = []
    if r.get("kosher"):
        out.append(f'<span class="badge {KOSHER_CLASS.get(r["kosher"], "")}">{E(r["kosher"])}</span>')
    for t in r.get("tags", []):
        out.append(f'<span class="badge {TAG_CLASS.get(t, "")}">{E(t)}</span>')
    return '<div class="badges">' + "".join(out) + "</div>"


def meta_line(r):
    return " · ".join(E(x) for x in (r.get("time"), r.get("yield")) if x)


def search_blob(r, tr):
    parts = [r["title"], r.get("source", ""), r["category"], r.get("kosher", ""), " ".join(r.get("tags", []))]
    if tr:
        for g in tr.get("ingredients", []):
            parts.extend(g.get("items", []))
    return norm(" ".join(parts).replace("[?]", " "))


TRANS = {r["id"]: load_transcription(r["id"]) for r in RECIPES}
for r in RECIPES:
    r["slug"] = CAT_SLUG[r["category"]]
    r["dims"] = jpeg_size(WEB / "images" / r["image"]) or (700, 700)


# ---------- layout ----------
FONTS = ('<link rel="preconnect" href="https://fonts.googleapis.com">'
         '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
         '<link href="https://fonts.googleapis.com/css2?family=Suez+One&family=Assistant:wght@400;500;600;700'
         '&family=Amatic+SC:wght@400;700&display=swap" rel="stylesheet">')


def header(p, current):
    def item(href, label, key):
        cur = ' aria-current="page"' if key == current else ""
        return f'<a href="{p}{href}"{cur}>{label}</a>'
    return (f'<a class="skip" href="#main">דלגו לתוכן</a>'
            f'<header class="site-header"><div class="wrap">'
            f'<a class="brand" href="{p}./">{E(SITE["title"])}</a>'
            f'<nav class="site-nav" aria-label="ראשי">'
            f'{item("recipes.html", "מתכונים", "recipes")}{item("categories.html", "קטגוריות", "categories")}'
            f'{item("about.html", "אודות", "about")}</nav>'
            f'<a class="cta" href="{p}add-recipe.html">＋ הוספת מתכון</a>'
            f'</div></header>')


def footer(p):
    return (f'<footer class="site-footer"><div class="wrap">'
            f'<span>{E(SITE["title"])} · <span class="bete">בתיאבון!</span></span>'
            f'<nav aria-label="קישורים נוספים"><a href="{p}about.html">אודות</a>'
            f'<a href="{p}add-recipe.html">הוספת מתכון</a><a href="{p}accessibility.html">הצהרת נגישות</a></nav>'
            f'</div></footer>')


def page(*, path, title, desc, body, current="", depth=0, og_image=None, body_attrs="", head_extra=""):
    p = "../" * depth
    url = SITE["url"] + path
    og_img = SITE["url"] + (og_image or SITE["og_image"])
    full_title = title if title == SITE["title"] else f'{title} — {SITE["title"]}'
    doc = f'''<!DOCTYPE html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(full_title)}</title>
<meta name="description" content="{E(desc)}">
<link rel="canonical" href="{E(url)}">
<meta name="theme-color" content="#6E5591">
<link rel="icon" href="{p}favicon.svg" type="image/svg+xml">
<meta property="og:type" content="website">
<meta property="og:locale" content="he_IL">
<meta property="og:site_name" content="{E(SITE["title"])}">
<meta property="og:title" content="{E(full_title)}">
<meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{E(url)}">
<meta property="og:image" content="{E(og_img)}">
<meta name="twitter:card" content="summary_large_image">
{FONTS}
<link rel="stylesheet" href="{p}assets/site.css">
<script src="{p}assets/site.js" defer></script>
{head_extra}</head>
<body{body_attrs}>
{header(p, current)}
{body}
{footer(p)}
</body>
</html>
'''
    out = WEB / path if path else WEB / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(doc, encoding="utf-8")


def card(r, p="", heading="h3", lazy=True):
    load = ' loading="lazy" decoding="async"' if lazy else ""
    tr = TRANS.get(r["id"])
    return (f'<a class="card" href="{p}recipes/{r["id"]}.html" data-id="{r["id"]}" data-cat="{r["slug"]}" '
            f'data-search="{E(search_blob(r, tr))}">'
            f'<img class="thumb" src="{p}images/{E(r["image"])}" alt="" width="400" height="300"{load}>'
            f'<div class="body"><{heading}>{E(r["title"])}</{heading}>'
            + (f'<p class="sub">— {E(r["source"])}</p>' if r.get("source") else "")
            + badges(r) + f'<div class="meta">{meta_line(r)}</div></div></a>')


def chips(with_counts=True, center=False):
    total = len(RECIPES)
    out = [f'<button type="button" class="chip" data-filter="all" aria-pressed="true">הכל'
           + (f'<span class="n">{total}</span>' if with_counts else "") + "</button>"]
    for c in CATS:
        n = sum(1 for r in RECIPES if r["category"] == c["name"])
        out.append(f'<button type="button" class="chip" data-filter="{c["slug"]}" aria-pressed="false">{E(c["name"])}'
                   + (f'<span class="n">{n}</span>' if with_counts else "") + "</button>")
    cls = "chips center" if center else "chips"
    return f'<div class="{cls}" role="group" aria-label="סינון לפי קטגוריה">' + "".join(out) + "</div>"


EMPTY = ('<p class="empty" data-empty>לא מצאנו מתכון כזה. נסו מילה אחרת, '
         'או <a href="add-recipe.html">שלחו לנו אותו</a>.</p>')


# ---------- pages ----------
def build_index():
    scatter = [("rina-chocolate.jpg", "top:340px;right:-40px;width:200px;height:150px;transform:rotate(8deg)"),
               ("tartlets.jpg", "top:900px;right:-60px;width:180px;height:220px;transform:rotate(-7deg)"),
               ("boyikos.jpg", "top:1700px;right:-30px;width:210px;height:140px;transform:rotate(5deg)"),
               ("caramel-pie.jpg", "top:520px;left:-50px;width:190px;height:230px;transform:rotate(-9deg)"),
               ("heli-meatballs.jpg", "top:1300px;left:-70px;width:230px;height:150px;transform:rotate(6deg)"),
               ("lemon-cookies.jpg", "top:2100px;left:-30px;width:180px;height:150px;transform:rotate(-5deg)")]
    sc = "".join(f'<img src="images/{f}" alt="" loading="lazy" style="{s}">' for f, s in scatter)
    cards = "".join(card(r, lazy=i >= 6) for i, r in enumerate(RECIPES))
    body = f'''<div class="bg-photo" style="background-image:url('{E(SITE["hero_bg"])}')" aria-hidden="true"></div>
<div class="bg-veil" aria-hidden="true"></div>
<div class="scatter" aria-hidden="true">{sc}</div>
<main id="main">
<section class="hero wrap">
<h1>{E(SITE["hero_title"])}</h1>
<p class="kicker">{E(SITE["hero_sub"])}</p>
<div class="surprise">
<button type="button" class="btn btn-accent" data-surprise>🎲 תפתיעו אותי</button>
<p class="surprise-out" data-surprise-out></p>
</div>
</section>
<section class="wrap" aria-labelledby="all-h">
<h2 id="all-h" class="sr-only">כל המתכונים</h2>
<div class="tools">{chips(center=True)}<p class="result-count" data-count role="status" aria-live="polite" style="text-align:center"></p></div>
<div class="grid" data-grid>{cards}</div>
{EMPTY}
</section>
</main>'''
    page(path="", title=SITE["title"], desc=SITE["description"], body=body, current="home")


def build_recipes():
    cards = "".join(card(r, lazy=i >= 6) for i, r in enumerate(RECIPES))
    body = f'''<main id="main" class="wrap">
<div class="page-head"><h1>כל המתכונים</h1>
<p class="kicker">{len(RECIPES)} מתכונים · חפשו לפי שם, מקור או מצרך</p></div>
<div class="tools">
<div class="search-box"><label for="q" class="sr-only">חיפוש מתכון</label>
<input id="q" type="search" placeholder="חיפוש מתכון… (למשל: גבינה, קציצות, פאי)" autocomplete="off"></div>
{chips()}
<p class="result-count" data-count role="status" aria-live="polite"></p>
</div>
<h2 class="sr-only">רשימת המתכונים</h2>
<div class="grid" data-grid>{cards}</div>
{EMPTY}
</main>'''
    page(path="recipes.html", title="כל המתכונים", current="recipes",
         desc=f'כל {len(RECIPES)} המתכונים של תמר במקום אחד — חיפוש לפי שם, מקור או מצרך, וסינון לפי קטגוריה.',
         body=body)


def build_categories():
    tabs, sections = [], []
    for c in CATS:
        group = [r for r in RECIPES if r["category"] == c["name"]]
        if not group:
            continue
        tabs.append(f'<a href="#{c["slug"]}">{E(c["name"])} ({len(group)})</a>')
        sections.append(f'<section class="cat-section" id="{c["slug"]}" aria-labelledby="h-{c["slug"]}">'
                        f'<div class="cat-head"><h2 id="h-{c["slug"]}">{E(c["name"])}</h2>'
                        f'<span class="n">{len(group)} מתכונים</span></div>'
                        f'<div class="grid">{"".join(card(r) for r in group)}</div></section>')
    body = f'''<main id="main" class="wrap">
<div class="page-head" id="top"><h1>קטגוריות</h1><p class="kicker">כל המתכונים, מסודרים לפי סוג</p></div>
<nav class="tabs" aria-label="קפיצה לקטגוריה">{"".join(tabs)}</nav>
{"".join(sections)}
<a class="to-top" href="#top">↑ לראש הדף</a>
</main>'''
    page(path="categories.html", title="קטגוריות", current="categories",
         desc="מתכוני המשפחה לפי קטגוריות: " + ", ".join(c["name"] for c in CATS) + ".", body=body)


def transcript_html(r, tr):
    if not tr or (not tr.get("ingredients") and not tr.get("steps")):
        return ('<section class="transcript" aria-labelledby="tr-h"><h2 id="tr-h">המתכון בכתב</h2>'
                '<p class="note">תמלול בכתב של המתכון יתווסף בקרוב. בינתיים אפשר לפתוח את הסריקה בגודל מלא.</p></section>')
    conf = tr.get("confidence")
    if conf == "verified":
        note = '<p class="note">התמלול נבדק מול הסריקה המקורית.</p>'
    else:
        note = ('<p class="note">התמלול נעשה אוטומטית מהסריקה ועדיין לא נבדק, אז ייתכנו בו טעויות. '
                'מילים <span class="unsure">מסומנות</span> הן לא ודאיות. במקרה של ספק, הסריקה היא המקור.'
                + (" חלקים מהסריקה קשים מאוד לקריאה." if conf == "low" else "") + "</p>")
    parts = ['<section class="transcript" aria-labelledby="tr-h"><h2 id="tr-h">המתכון בכתב</h2>', note]
    groups = tr.get("ingredients") or []
    if groups:
        parts.append("<h3>מצרכים</h3>")
        for g in groups:
            if g.get("section"):
                parts.append(f'<p><strong>{mark_unsure(g["section"])}</strong></p>')
            parts.append("<ul>" + "".join(f"<li>{mark_unsure(x)}</li>" for x in g.get("items", [])) + "</ul>")
    steps = [re.sub(r"^\s*\d+\s*[.)]\s*", "", s) for s in tr.get("steps", [])]
    if steps:
        parts.append("<h3>אופן ההכנה</h3><ol>" + "".join(f"<li>{mark_unsure(s)}</li>" for s in steps) + "</ol>")
    joined = " ".join(steps)
    notes = [n for n in tr.get("notes", []) if n.strip() and n.strip() not in joined]
    if notes:
        parts.append("<h3>הערות מהדף</h3><ul>" + "".join(f"<li>{mark_unsure(n)}</li>" for n in notes) + "</ul>")
    parts.append("</section>")
    return "".join(parts)


def build_recipe_pages():
    keep = {f'{r["id"]}.html' for r in RECIPES}
    for stale in (WEB / "recipes").glob("recipe-*.html"):
        if stale.name not in keep:
            stale.unlink()
    n = len(RECIPES)
    for i, r in enumerate(RECIPES):
        tr = TRANS.get(r["id"])
        prev_r, next_r = RECIPES[(i - 1) % n], RECIPES[(i + 1) % n]
        related = [x for x in RECIPES if x["category"] == r["category"] and x["id"] != r["id"]][:3]
        w, h = r["dims"]
        img = f'../images/{E(r["image"])}'
        rel_html = ""
        if related:
            rel_html = (f'<section class="related" aria-labelledby="rel-h"><h2 id="rel-h">עוד ב{E(r["category"])}</h2>'
                        f'<div class="grid">{"".join(card(x, p="../") for x in related)}</div></section>')
        body = f'''<main id="main" class="wrap recipe-wrap">
<div class="pad">
<nav class="crumbs" aria-label="פירורי לחם"><a href="../recipes.html">כל המתכונים</a> ›
<a href="../recipes.html#cat={r["slug"]}">{E(r["category"])}</a></nav>
<header class="recipe-head">
<h1>{E(r["title"])}</h1>
{f'<p class="kicker">— {E(r["source"])}</p>' if r.get("source") else ""}
{badges(r)}
<p class="meta">{meta_line(r)}</p>
</header>
<div class="actions">
<button type="button" class="btn btn-brand" data-cook data-src="{img}">👩‍🍳 מצב בישול</button>
<button type="button" class="btn btn-line made-btn" data-made aria-pressed="false">✓ הכנתי את זה!</button>
<button type="button" class="btn btn-wa" data-share>📤 שיתוף</button>
<button type="button" class="btn btn-line" data-print>🖨 הדפסה</button>
<p class="made-msg" data-made-msg role="status"></p>
</div>
</div>
<figure class="scan">
<a class="zoom" href="{img}" title="פתיחת הסריקה בגודל מלא"><img src="{img}" width="{w}" height="{h}" alt="סריקת המתכון המקורי: {E(r["title"])}"></a>
<figcaption>הסריקה המקורית · {E(r.get("source") or "מהמשפחה")}</figcaption>
</figure>
<div class="pad">
<a class="zoom-hint" href="{img}">🔍 פתיחת הסריקה בגודל מלא</a>
{transcript_html(r, tr)}
<nav class="pager" aria-label="מתכונים נוספים">
<a rel="prev" href="{prev_r["id"]}.html">→ הקודם: {E(prev_r["title"])}</a>
<a rel="next" href="{next_r["id"]}.html">הבא: {E(next_r["title"])} ←</a>
</nav>
{rel_html}
<a class="back-link" data-back href="../recipes.html">→ חזרה לכל המתכונים</a>
</div>
</main>'''
        desc_bits = [f'{r["title"]}: מתכון משפחתי' + (f' — {r["source"]}' if r.get("source") else "") + "."]
        if meta_line(r):
            desc_bits.append(" · ".join(x for x in (r.get("time"), r.get("yield")) if x) + ".")
        desc_bits.append(f'{r.get("kosher", "")}. הסריקה המקורית ותמלול בכתב.')
        page(path=f'recipes/{r["id"]}.html', title=r["title"], desc=" ".join(desc_bits), body=body, depth=1,
             og_image=f'images/{r["image"]}', body_attrs=f' data-page="recipe" data-id="{r["id"]}"')


def build_about():
    body = '''<main id="main" class="wrap">
<div class="page-head"><h1>אודות</h1><p class="kicker">איך נולד הפנקס הזה</p></div>
<div class="prose panel">
<p>כאן נאספו מתכוני המשפחה, ממש כמו שהם חיו אצלנו במטבח: בכתב יד בפנקס הישן, בקלסר מלא דפים, על פתקים צהובים וגזירי עיתון.</p>
<p>יש כאן עוגות של דבי יעל, טארטלטים של חני פיין, הקציצות של חלי לופצ׳י ופאי הרועים של אמא, ועוד מתכונים שעוברים מיד ליד כבר שנים.</p>
<p>לכל מתכון צירפנו את הסריקה המקורית, כדי שתראו את הכתב, הכתמים והתיקונים בשוליים. גם הם חלק מהטעם. מתחת לסריקה יש תמלול בכתב, כדי שיהיה קל לקרוא, לחפש ולהדפיס.</p>
<p>יש לכם מתכון משפחתי שמגיע לו מקום כאן? <a href="add-recipe.html">שלחו לנו אותו</a>. אפשר גם פשוט לצלם דף מהמחברת.</p>
<p class="bete">בתיאבון, ושיהיו לכם שולחנות מלאים!</p>
</div>
</main>'''
    page(path="about.html", title="אודות", current="about",
         desc="על המתכונים של תמר: מתכוני משפחה מהפנקס, מהקלסר, מפתקים וגזירי עיתון, עם הסריקות המקוריות.",
         body=body)


def build_accessibility():
    body = f'''<main id="main" class="wrap">
<div class="page-head"><h1>הצהרת נגישות</h1></div>
<div class="prose panel">
<p>"המתכונים של תמר" הוא אתר משפחתי. חשוב לנו שכל בני המשפחה והחברים, כולל אנשים עם מוגבלות, יוכלו להשתמש בו בנוחות.</p>
<h2>רמת ההתאמה</h2>
<p>פעלנו להתאים את האתר לדרישות התקן הישראלי ת"י 5568, המבוסס על הנחיות WCAG 2.1 ברמה AA. ההתאמה נבדקה בבדיקה עצמית.</p>
<h2>מה נעשה באתר</h2>
<ul>
<li>ניווט מלא במקלדת, קישור "דלגו לתוכן" וסימון ברור של הרכיב שבפוקוס.</li>
<li>ניגודיות צבעים שעומדת בדרישות התקן, וגודל טקסט נוח לקריאה.</li>
<li>כפתורים ואזורי לחיצה בגודל של 44 פיקסלים לפחות, ותצוגה מותאמת לטלפון.</li>
<li>תוויות לכל שדות הטופס, והודעות שקוראי מסך מקריאים בזמן חיפוש וסינון.</li>
<li>תמלול בכתב של המתכונים הסרוקים, ואפשרות לפתוח כל סריקה בגודל מלא.</li>
<li>כיבוד הגדרת "הפחתת תנועה" של המכשיר.</li>
</ul>
<h2>מגבלות ידועות</h2>
<ul>
<li>התמלול של המתכונים נעשה אוטומטית ועדיין לא נבדק במלואו, ולכן ייתכנו בו טעויות. מילים לא ודאיות מסומנות.</li>
<li>חלק מהסריקות המקוריות ברזולוציה נמוכה וקשות לקריאה.</li>
</ul>
<h2>נתקלתם בבעיה?</h2>
<p>אם נתקלתם בבעיית נגישות באתר, נשמח לשמוע ולתקן. פרטי הקשר של רכז/ת הנגישות יפורסמו כאן בקרוב.</p>
<p>ההצהרה עודכנה בתאריך {date.today().strftime("%d/%m/%Y")}.</p>
</div>
</main>'''
    page(path="accessibility.html", title="הצהרת נגישות", desc="הצהרת הנגישות של האתר המתכונים של תמר.", body=body)


def build_add():
    fs = SITE.get("formspree_id", "")
    opts = "".join(f"<option>{E(c['name'])}</option>" for c in CATS)
    if fs:
        notice = "המתכון נשלח <b>לאישור</b>. אחרי בדיקה קטנה הוא יתווסף לאתר."
    else:
        notice = ("השליחה נעשית <b>בוואטסאפ</b>: אחרי הלחיצה ייפתח וואטסאפ עם המתכון. "
                  "שם תוכלו לבחור לשלוח לתמר ולצרף תמונה של הדף.")
    body = f'''<main id="main" class="wrap">
<div class="page-head"><h1>הוספת מתכון</h1><p class="kicker">יש לכם מתכון משפחתי? שלחו אותו לתמר 🧡</p></div>
<div class="form">
<p class="notice">{notice}</p>
<div id="form-ok" class="status ok" role="status" tabindex="-1" hidden>
<p data-text>🧡 תודה רבה! המתכון הגיע לתמר. אחרי בדיקה קטנה הוא יעלה לאתר. אם השארתם כתובת מייל, נעדכן אתכם כשהוא באוויר.</p>
<a href="add-recipe.html">לשליחת מתכון נוסף</a></div>
<div id="form-err" class="status err" role="alert" tabindex="-1" hidden>
<p data-text>אופס, השליחה לא הצליחה. נסו שוב בעוד רגע.</p></div>
<form data-recipe-form data-formspree="{E(fs)}">
<input type="hidden" name="_subject" value="מתכון חדש מהאתר של תמר">
<fieldset><legend>על המתכון</legend>
<div class="field"><label for="f-name">שם המתכון <span class="req" aria-hidden="true">*</span><span class="sr-only">(חובה)</span></label>
<input id="f-name" name="שם המתכון" required aria-required="true" placeholder="למשל: עוגת גבינה של סבתא"></div>
<div class="row2">
<div class="field"><label for="f-cat">קטגוריה</label>
<select id="f-cat" name="קטגוריה"><option value="">בחרו קטגוריה</option>{opts}<option>לא בטוח/ה</option></select></div>
<div class="field"><label for="f-kosher">כשרות</label>
<select id="f-kosher" name="כשרות"><option value="">בחרו</option><option>חלבי</option><option>פרווה</option><option>בשרי</option></select></div>
</div>
<div class="row2">
<div class="field"><label for="f-time">זמן הכנה</label><input id="f-time" name="זמן הכנה" placeholder="למשל: שעה"></div>
<div class="field"><label for="f-yield">כמות / תבנית</label><input id="f-yield" name="כמות" placeholder="למשל: תבנית מלבנית"></div>
</div>
<div class="field"><label for="f-src">של מי המתכון?</label><input id="f-src" name="מקור" placeholder="למשל: מהקלסר של סבתא"></div>
</fieldset>
<fieldset><legend>המתכון</legend>
<p class="hint">אין זמן להקליד? אפשר להשאיר את השדות האלה ריקים ולשלוח תמונה של הדף.</p>
<div class="field"><label for="f-ing">מצרכים</label><textarea id="f-ing" name="מצרכים" placeholder="שורה לכל מצרך…"></textarea></div>
<div class="field"><label for="f-steps">אופן ההכנה</label><textarea id="f-steps" name="אופן ההכנה" placeholder="שלב אחרי שלב…"></textarea></div>
<div class="field"><label for="f-img">קישור לתמונה (לא חובה)</label>
<input id="f-img" type="url" name="קישור לתמונה" placeholder="https://" aria-describedby="f-img-hint">
<p class="hint" id="f-img-hint">אין תמונה ברשת? אפשר לצרף אותה בוואטסאפ.</p></div>
</fieldset>
<fieldset><legend>מי שולח?</legend>
<div class="row2">
<div class="field"><label for="f-sender">השם שלכם <span class="req" aria-hidden="true">*</span><span class="sr-only">(חובה)</span></label>
<input id="f-sender" name="שם השולח" required aria-required="true" autocomplete="name"></div>
<div class="field"><label for="f-email">אימייל לעדכון (לא חובה)</label>
<input id="f-email" type="email" name="email" autocomplete="email" placeholder="name@example.com"></div>
</div>
<div class="field"><label for="f-notes">הערות או הסיפור מאחורי המתכון (לא חובה)</label>
<textarea id="f-notes" name="הערות" style="min-height:80px"></textarea></div>
</fieldset>
<button type="submit" class="btn btn-brand">שליחה לאישור</button>
</form>
</div>
</main>'''
    page(path="add-recipe.html", title="הוספת מתכון", desc="שלחו מתכון משפחתי לאתר המתכונים של תמר.", body=body)


def build_404():
    body = '''<main id="main" class="wrap">
<div class="page-head"><h1>אופס, הדף לא נמצא</h1><p class="kicker">אולי המתכון עבר מגירה…</p></div>
<div class="prose panel"><p>הדף שחיפשתם לא קיים. אפשר לחזור ל<a href="./">דף הבית</a> או לחפש ב<a href="recipes.html">כל המתכונים</a>.</p></div>
</main>'''
    base = re.sub(r"^https?://[^/]+", "", SITE["url"])
    page(path="404.html", title="הדף לא נמצא", desc="הדף לא נמצא.", body=body, head_extra=f'<base href="{E(base)}">\n')


def build_static_files():
    urls = ["", "recipes.html", "categories.html", "about.html", "add-recipe.html", "accessibility.html"]
    urls += [f'recipes/{r["id"]}.html' for r in RECIPES]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    sm += [f"<url><loc>{E(SITE['url'] + u)}</loc><lastmod>{TODAY}</lastmod></url>" for u in urls]
    sm.append("</urlset>")
    (WEB / "sitemap.xml").write_text("\n".join(sm) + "\n", encoding="utf-8")
    (WEB / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE['url']}sitemap.xml\n", encoding="utf-8")
    (WEB / "favicon.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
        '<rect width="64" height="64" rx="14" fill="#6E5591"/>'
        '<text x="32" y="46" font-size="40" text-anchor="middle" fill="#FBF8F1" '
        'font-family="Suez One, Georgia, serif">ת</text></svg>\n', encoding="utf-8")


if __name__ == "__main__":
    build_index()
    build_recipes()
    build_categories()
    build_recipe_pages()
    build_about()
    build_accessibility()
    build_add()
    build_404()
    build_static_files()
    have = sum(1 for v in TRANS.values() if v)
    print(f"built {len(RECIPES)} recipes, {have} with transcriptions -> {WEB}")
