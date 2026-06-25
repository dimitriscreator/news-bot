# =============================================================================
# builder.py — Φτιάχνει την HTML σελίδα και το .md αρχείο του report
# =============================================================================

import datetime
import html as html_lib

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
    months = ["Ιανουαρίου","Φεβρουαρίου","Μαρτίου","Απριλίου","Μαΐου",
              "Ιουνίου","Ιουλίου","Αυγούστου","Σεπτεμβρίου","Οκτωβρίου",
              "Νοεμβρίου","Δεκεμβρίου"]
    return f"{d.day} {months[d.month - 1]} {d.year}"


def build_html(report_data: dict, date: datetime.date,
               cost_summary: str = "") -> str:
    date_str = _greek_date(date)
    sections = []

    for category, articles in report_data.items():
        if not articles:
            continue
        label, icon = CATEGORY_LABELS.get(category, (category, "•"))

        cards = []
        for art in articles:
            title    = html_lib.escape(art["title"])
            source   = html_lib.escape(art["source"])
            url      = html_lib.escape(art["url"])
            analysis = art["analysis_html"]

            cards.append(f"""
            <article class="card">
              <h3 class="card-title">{title}</h3>
              <div class="card-meta">
                <span class="card-source">{source}</span>
                <a class="source-link-top" href="{url}" target="_blank" rel="noopener">
                  → Διάβασε το πρωτότυπο άρθρο
                </a>
              </div>
              <div class="analysis">{analysis}</div>
            </article>""")

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

    cost_html = ""
    if cost_summary:
        cost_html = f"""
    <div class="cost-badge">
      💰 Κόστος report: <strong>{html_lib.escape(cost_summary)}</strong>
    </div>"""

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
    --ink:        #0f1b2d;
    --paper:      #faf7f0;
    --paper-card: #ffffff;
    --gold:       #b07a2c;
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

  /* ΕΠΙΚΕΦΑΛΙΔΑ */
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

  /* ΠΕΡΙΕΧΟΜΕΝΟ */
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

  /* ΚΑΡΤΑ ΑΡΘΡΟΥ */
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
    margin: 0 0 8px;
    color: var(--ink);
  }}

  /* Meta row: πηγή + link πρωτοτύπου στην κορυφή */
  .card-meta {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
    margin-bottom: 18px;
    padding-bottom: 14px;
    border-bottom: 1px solid var(--gold-soft);
  }}
  .card-source {{
    font-size: 13px;
    color: var(--gold);
    font-weight: 600;
    letter-spacing: 0.03em;
  }}
  /* Link στην ΚΟΡΥΦΗ της κάρτας — εμφανές κουμπί */
  .source-link-top {{
    font-size: 13px;
    font-weight: 600;
    color: var(--ink);
    background: var(--gold-soft);
    text-decoration: none;
    padding: 4px 10px;
    border-radius: 20px;
    white-space: nowrap;
    transition: background 0.15s;
  }}
  .source-link-top:hover {{ background: var(--gold); color: #fff; }}

  /* ΑΝΑΛΥΣΗ */
  .analysis {{ color: var(--text); }}
  .analysis p {{ margin: 0 0 14px; }}
  .analysis strong {{ color: var(--ink); }}
  .analysis em {{ color: var(--text-soft); font-style: italic; }}

  /* Block labels (εικονίδια-τίτλοι ενοτήτων) */
  .analysis .block-label {{
    display: block;
    font-weight: 700;
    color: var(--ink);
    margin: 22px 0 6px;
    font-size: 15px;
    letter-spacing: 0.02em;
    font-family: 'Inter', sans-serif;
  }}

  /* Αριθμημένα σημεία ①②③ */
  .analysis .numbered-point {{
    margin: 6px 0 6px 18px;
    padding-left: 8px;
    border-left: 3px solid var(--gold-soft);
    color: var(--text);
  }}

  /* ΚΟΣΤΟΣ BADGE */
  .cost-badge {{
    margin: 30px 0 0;
    padding: 10px 16px;
    background: var(--paper-card);
    border: 1px solid var(--line);
    border-radius: 8px;
    font-size: 13px;
    color: var(--text-soft);
    text-align: center;
  }}
  .cost-badge strong {{ color: var(--text); }}

  .footer {{
    text-align: center;
    color: var(--text-soft);
    font-size: 13px;
    margin-top: 30px;
    padding-top: 22px;
    border-top: 1px solid var(--line);
  }}

  @media (max-width: 480px) {{
    body {{ font-size: 16px; }}
    .masthead h1 {{ font-size: 25px; }}
    .card {{ padding: 20px 17px; }}
    .card-meta {{ flex-direction: column; align-items: flex-start; }}
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
    {cost_html}
    <div class="footer">
      Αυτόματη ανάλυση · Δημιουργήθηκε για προσωπική χρήση<br>
      Ανάλυση, όχι είδηση — εργαλεία σκέψης για κάθε πρωί
    </div>
  </main>
</body>
</html>"""


def build_markdown(report_data: dict, date: datetime.date,
                   cost_summary: str = "") -> str:
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
            lines.append(f"*Πηγή: [{art['source']}]({art['url']})*")
            lines.append("")
            lines.append(art.get("analysis_md", art["title"]))
            lines.append("")
            lines.append(f"🔗 [Αυθεντικό άρθρο]({art['url']})")
            lines.append("\n---\n")

    if cost_summary:
        lines.append(f"\n---\n💰 **Κόστος report:** {cost_summary}")

    return "\n".join(lines)
