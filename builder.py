# =============================================================================
# builder.py — Φτιάχνει την HTML σελίδα και το .md αρχείο του report
# =============================================================================
# Δουλειά:
#   1) build_html()  → φτιάχνει μια όμορφη, ευανάγνωστη ιστοσελίδα με ΟΛΗ
#      την ανάλυση (αυτή ανοίγει στον browser με ένα πάτημα από το Telegram)
#   2) build_markdown() → φτιάχνει το .md αρχείο για το Obsidian αργότερα
#
# Δεν χρειάζεται να αγγίξεις αυτό το αρχείο για να αλλάξεις περιεχόμενο —
# μόνο αν θες να αλλάξεις την ΕΜΦΑΝΙΣΗ της σελίδας.
# =============================================================================

import datetime
import html as html_lib

# Φιλικά ελληνικά ονόματα + εικονίδιο για κάθε κατηγορία
CATEGORY_LABELS = {
    "POLITICS":                ("Πολιτική", "🏛"),
    "GEOPOLITICS_DIPLOMACY":   ("Γεωπολιτική & Διπλωματία", "🌍"),
    "ECONOMICS_FINANCE":       ("Οικονομία & Χρηματοοικονομικά", "📊"),
    "INTL_BUSINESS_STRATEGY":  ("Διεθνές Business — Strategy & Innovation", "🎯"),
    "AI":                      ("Τεχνητή Νοημοσύνη", "🤖"),
    "STOCK_MARKETS":           ("Χρηματιστήρια", "📈"),
    "PHILOSOPHICAL_OPINIONS":  ("Φιλοσοφικές Απόψεις", "💭"),
}


def _greek_date(d: datetime.date) -> str:
    """Μετατρέπει μια ημερομηνία σε ελληνικό κείμενο, π.χ. '25 Ιουνίου 2026'."""
    months = ["Ιανουαρίου", "Φεβρουαρίου", "Μαρτίου", "Απριλίου", "Μαΐου",
              "Ιουνίου", "Ιουλίου", "Αυγούστου", "Σεπτεμβρίου", "Οκτωβρίου",
              "Νοεμβρίου", "Δεκεμβρίου"]
    return f"{d.day} {months[d.month - 1]} {d.year}"


# =============================================================================
# Η ΙΣΤΟΣΕΛΙΔΑ (HTML + CSS)
# =============================================================================

def build_html(report_data: dict, date: datetime.date) -> str:
    """
    report_data: λεξικό { κατηγορία: [ {title, source, url, analysis_html}, ... ] }
    Επιστρέφει ολόκληρη την HTML σελίδα ως κείμενο.
    """
    date_str = _greek_date(date)

    # --- Φτιάχνουμε το σώμα: ένα τμήμα ανά κατηγορία ---
    sections = []
    for category, articles in report_data.items():
        if not articles:
            continue
        label, icon = CATEGORY_LABELS.get(category, (category, "•"))

        cards = []
        for art in articles:
            title  = html_lib.escape(art["title"])
            source = html_lib.escape(art["source"])
            url    = html_lib.escape(art["url"])
            # Η ανάλυση έρχεται ήδη ως HTML (paragraphs), δεν την escape-άρουμε
            analysis = art["analysis_html"]

            cards.append(f"""
            <article class="card">
              <h3 class="card-title">{title}</h3>
              <div class="card-source">{source}</div>
              <div class="analysis">{analysis}</div>
              <a class="source-link" href="{url}" target="_blank" rel="noopener">
                Διάβασε το αυθεντικό άρθρο στην πηγή →
              </a>
            </article>""")

        # Το anchor id χρησιμοποιείται για τα links ανά κατηγορία στο Telegram
        anchor = category.lower().replace("_", "-")
        sections.append(f"""
        <section class="category" id="{anchor}">
          <div class="category-header">
            <span class="category-icon">{icon}</span>
            <h2 class="category-name">{label}</h2>
          </div>
          {"".join(cards)}
        </section>""")

    body = "".join(sections)

    # --- Το πλήρες HTML με ενσωματωμένο στυλ ---
    return f"""<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Πρωινό Δελτίο Ανάλυσης — {date_str}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,400;0,9..144,600;0,9..144,700;1,9..144,400&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --ink:        #0f1b2d;   /* βαθύ navy — κύρος */
    --paper:      #faf7f0;   /* ζεστό off-white — ξεκούραστο */
    --paper-card: #ffffff;
    --gold:       #b07a2c;   /* κεχριμπαρένιο accent */
    --gold-soft:  #e9d9b8;
    --text:       #1d2b3a;
    --text-soft:  #5a6b7d;
    --line:       #e4ddd0;
  }}

  * {{ box-sizing: border-box; }}

  body {{
    margin: 0;
    background: var(--paper);
    color: var(--text);
    font-family: 'Inter', system-ui, sans-serif;
    font-size: 17px;
    line-height: 1.7;
    -webkit-font-smoothing: antialiased;
  }}

  /* --- ΕΠΙΚΕΦΑΛΙΔΑ --- */
  .masthead {{
    background: var(--ink);
    color: var(--paper);
    padding: 38px 22px 30px;
    text-align: center;
  }}
  .masthead .eyebrow {{
    font-size: 12px;
    letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--gold-soft);
    margin-bottom: 10px;
  }}
  .masthead h1 {{
    font-family: 'Fraunces', Georgia, serif;
    font-weight: 600;
    font-size: 30px;
    line-height: 1.15;
    margin: 0 0 8px;
  }}
  .masthead .date {{
    font-style: italic;
    color: var(--gold-soft);
    font-family: 'Fraunces', serif;
    font-size: 17px;
  }}

  /* --- ΠΕΡΙΕΧΟΜΕΝΟ --- */
  .wrap {{ max-width: 720px; margin: 0 auto; padding: 8px 18px 60px; }}

  .category {{ margin-top: 44px; }}
  .category-header {{
    display: flex;
    align-items: center;
    gap: 12px;
    padding-bottom: 12px;
    border-bottom: 2px solid var(--gold);
    margin-bottom: 22px;
  }}
  .category-icon {{ font-size: 26px; }}
  .category-name {{
    font-family: 'Fraunces', serif;
    font-weight: 600;
    font-size: 22px;
    margin: 0;
    color: var(--ink);
  }}

  /* --- ΚΑΡΤΑ ΑΡΘΡΟΥ --- */
  .card {{
    background: var(--paper-card);
    border: 1px solid var(--line);
    border-radius: 14px;
    padding: 24px 22px;
    margin-bottom: 22px;
    box-shadow: 0 1px 3px rgba(15,27,45,0.04);
  }}
  .card-title {{
    font-family: 'Fraunces', serif;
    font-weight: 600;
    font-size: 21px;
    line-height: 1.3;
    margin: 0 0 4px;
    color: var(--ink);
  }}
  .card-source {{
    font-size: 13px;
    color: var(--gold);
    font-weight: 600;
    letter-spacing: 0.03em;
    margin-bottom: 18px;
  }}

  .analysis {{ color: var(--text); }}
  .analysis p {{ margin: 0 0 14px; }}
  /* Οι μικροί τίτλοι μέσα στην ανάλυση (🏛 ΠΛΑΙΣΙΟ, 📖 ΠΙΣΩ ΑΠΟ... κ.λπ.) */
  .analysis .block-label {{
    display: block;
    font-weight: 600;
    color: var(--ink);
    margin: 20px 0 6px;
    font-size: 15px;
    letter-spacing: 0.02em;
  }}

  .source-link {{
    display: inline-block;
    margin-top: 12px;
    color: var(--gold);
    font-weight: 600;
    text-decoration: none;
    border-bottom: 1px solid var(--gold-soft);
    padding-bottom: 1px;
  }}
  .source-link:hover {{ border-bottom-color: var(--gold); }}

  .footer {{
    text-align: center;
    color: var(--text-soft);
    font-size: 13px;
    margin-top: 50px;
    padding-top: 22px;
    border-top: 1px solid var(--line);
  }}

  @media (max-width: 480px) {{
    body {{ font-size: 16px; }}
    .masthead h1 {{ font-size: 25px; }}
    .card {{ padding: 20px 17px; }}
  }}
</style>
</head>
<body>
  <header class="masthead">
    <div class="eyebrow">Πρωινό Δελτίο Ανάλυσης</div>
    <h1>Πίσω από τις Γραμμές</h1>
    <div class="date">{date_str}</div>
  </header>
  <main class="wrap">
    {body}
    <div class="footer">
      Αυτόματη ανάλυση · Δημιουργήθηκε για προσωπική χρήση<br>
      Ανάλυση, όχι είδηση — εργαλεία σκέψης για κάθε πρωί
    </div>
  </main>
</body>
</html>"""


# =============================================================================
# ΤΟ MARKDOWN ΑΡΧΕΙΟ (για Obsidian αργότερα)
# =============================================================================

def build_markdown(report_data: dict, date: datetime.date) -> str:
    """Φτιάχνει ένα καθαρό .md αρχείο με όλη την ανάλυση της ημέρας."""
    date_iso = date.isoformat()
    lines = [
        "---",
        f"date: {date_iso}",
        "type: news-report",
        "tags: [daily-news, analysis]",
        "---",
        "",
        f"# 📰 Πρωινό Δελτίο Ανάλυσης — {_greek_date(date)}",
        "",
    ]

    for category, articles in report_data.items():
        if not articles:
            continue
        label, icon = CATEGORY_LABELS.get(category, (category, "•"))
        lines.append(f"\n## {icon} {label}\n")

        for art in articles:
            lines.append(f"### {art['title']}")
            lines.append(f"*Πηγή: {art['source']}*")
            lines.append("")
            # Η ανάλυση σε markdown (η plain εκδοχή, χωρίς HTML tags)
            lines.append(art.get("analysis_md", art["title"]))
            lines.append("")
            lines.append(f"🔗 [Αυθεντικό άρθρο]({art['url']})")
            lines.append("\n---\n")

    return "\n".join(lines)
