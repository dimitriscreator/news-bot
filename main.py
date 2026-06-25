# =============================================================================
# main.py — Το «αφεντικό» που τρέχει όλη τη διαδικασία
# =============================================================================
# Η ροή: Συλλέκτης → Καθαριστής → Αναλυτής (Gemini) → Ταχυδρόμος (Telegram)
# =============================================================================

# --- Δανειζόμαστε έτοιμα εργαλεία (libraries) ---
import os               # για να διαβάζουμε τα "secrets" (κλειδιά)
import time             # για μικρές παύσεις ανάμεσα στις κλήσεις
import datetime         # για την ημερομηνία στο report
import feedparser       # για να διαβάζουμε RSS feeds
from google import genai  # το ΝΕΟ επίσημο εργαλείο της Google για Gemini
import requests         # για να στέλνουμε μηνύματα στο Telegram

# --- Δανειζόμαστε τα δικά μας αρχεία ---
from feeds import FEEDS, ARTICLES_PER_FEED, TOP_PER_CATEGORY
import prompt as P


# =============================================================================
# ΡΥΘΜΙΣΕΙΣ — άλλαξε εδώ αν θες, χωρίς να ξέρεις κώδικα
# =============================================================================

# Ποια μοντέλα Gemini χρησιμοποιούμε.
# Δοκιμάζει ΠΡΩΤΑ το πρωτεύον. Αν είναι γεμάτο (503 "high demand"),
# πέφτει αυτόματα στο εφεδρικό — ώστε το report να μη χαλάει ποτέ.
MODEL_PRIMARY  = "gemini-3.5-flash"   # καλύτερο, αλλά πιο συχνά "γεμάτο"
MODEL_FALLBACK = "gemini-2.5-flash"   # πιο σταθερό εφεδρικό

# Όνομα του secret με το κλειδί (όπως το έβαλες στο GitHub)
API_KEY_NAME = "GEMINI_API_KEY_NEWS_AGENT"

# "Γραβάτα" — λέμε στις ειδησεογραφικές σελίδες ότι είμαστε κανονικός browser.
# Κάποιες πηγές μπλοκάρουν προγράμματα χωρίς αυτό (σφάλμα 403 "Forbidden").
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/120.0.0.0 Safari/537.36")


# =============================================================================
# ΜΗΧΑΝΗ 1 — Ο ΣΥΛΛΕΚΤΗΣ
# Δουλειά: μπαίνει σε κάθε RSS feed και μαζεύει τα τελευταία άρθρα
# =============================================================================

def collect_articles(category: str) -> list:
    """
    Παίρνει το όνομα μιας κατηγορίας (π.χ. "AI") και επιστρέφει
    μια λίστα με όλα τα άρθρα που βρήκε από τις πηγές της.
    """
    articles = []
    feed_urls = FEEDS[category]  # οι πηγές αυτής της κατηγορίας

    for url in feed_urls:
        try:
            # Διαβάζουμε το RSS feed (με "γραβάτα" για να μη μας μπλοκάρουν)
            parsed = feedparser.parse(url, agent=USER_AGENT)
            source_name = parsed.feed.get("title", url)

            # Παίρνουμε μέχρι ARTICLES_PER_FEED άρθρα από κάθε πηγή
            for entry in parsed.entries[:ARTICLES_PER_FEED]:
                articles.append({
                    "title": entry.get("title", "Χωρίς τίτλο"),
                    "url": entry.get("link", ""),
                    "source": source_name,
                    # Το RSS δίνει συνήθως μια σύνοψη — την κρατάμε
                    "content": entry.get("summary", ""),
                })
        except Exception as e:
            # Αν μια πηγή είναι προσωρινά χαλασμένη, την προσπερνάμε
            # αντί να σταματήσει όλο το πρόγραμμα
            print(f"   ⚠️  Πρόβλημα με πηγή {url}: {e}")
            continue

    return articles


# =============================================================================
# ΜΗΧΑΝΗ 2 — Ο ΚΑΘΑΡΙΣΤΗΣ
# Δουλειά: πετάει διπλότυπα και άρθρα χωρίς ουσία
# =============================================================================

def clean_articles(articles: list) -> list:
    """
    Παίρνει τη λίστα άρθρων και:
    - πετάει διπλότυπα (ίδιος ή σχεδόν ίδιος τίτλος)
    - πετάει άρθρα χωρίς URL ή με άδειο τίτλο
    """
    seen_titles = set()   # "ημερολόγιο" με τίτλους που έχουμε ήδη δει
    cleaned = []

    for article in articles:
        title = article["title"].strip()

        # Πέτα ό,τι δεν έχει τίτλο ή σύνδεσμο
        if not title or not article["url"]:
            continue

        # Φτιάχνουμε μια "απλοποιημένη" εκδοχή του τίτλου για σύγκριση
        # (πεζά + πρώτες 50 λέξεις-χαρακτήρες) ώστε να πιάνουμε σχεδόν-διπλότυπα
        fingerprint = title.lower()[:60]

        if fingerprint in seen_titles:
            continue  # το έχουμε ξαναδεί — προσπέρασε

        seen_titles.add(fingerprint)
        cleaned.append(article)

    return cleaned


# =============================================================================
# ΜΗΧΑΝΗ 3 — Ο ΑΝΑΛΥΤΗΣ (Gemini)
# Δουλειά: (α) διαλέγει τα top άρθρα, (β) γράφει την πλήρη ανάλυση
# =============================================================================

def make_gemini_client():
    """Φτιάχνει τη σύνδεση με το Gemini, διαβάζοντας το κλειδί από τα secrets."""
    api_key = os.environ.get(API_KEY_NAME)
    if not api_key:
        raise RuntimeError(
            f"Δεν βρέθηκε το κλειδί '{API_KEY_NAME}'. "
            f"Σιγουρέψου ότι το έβαλες στα GitHub Secrets."
        )
    return genai.Client(api_key=api_key)


def _call_one_model(client, model_name, prompt_text, config):
    """
    Καλεί ΕΝΑ συγκεκριμένο μοντέλο, με exponential backoff:
    αν βγει προσωρινό σφάλμα (503/429), περιμένει 2s, 4s, 8s... και ξαναδοκιμάζει.
    Επιστρέφει το κείμενο, ή πετάει σφάλμα αν αποτύχουν όλες οι προσπάθειες.
    """
    max_attempts = 4
    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt_text,
                config=config,
            )
            return response.text
        except Exception as e:
            msg = str(e)
            is_retryable = any(code in msg for code in
                               ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED",
                                "500", "504"))
            if is_retryable and attempt < max_attempts - 1:
                wait = 2 ** (attempt + 1)   # 2, 4, 8 δευτερόλεπτα
                print(f"      ⏳ {model_name}: προσωρινό σφάλμα — περιμένω {wait}s "
                      f"({attempt + 1}/{max_attempts})...")
                time.sleep(wait)
                continue
            raise   # δεν είναι retryable ή τελείωσαν οι προσπάθειες


def ask_gemini(client, prompt_text: str, system_text: str = "") -> str:
    """
    Στέλνει ένα ερώτημα στο Gemini.
    Στρατηγική διπλού διχτυού ασφαλείας:
      1) Δοκιμάζει το ΠΡΩΤΕΥΟΝ μοντέλο (με backoff).
      2) Αν αυτό αποτύχει τελείως, πέφτει στο ΕΦΕΔΡΙΚΟ (με backoff).
    """
    from google.genai import types

    config = None
    if system_text:
        config = types.GenerateContentConfig(system_instruction=system_text)

    # --- Προσπάθεια 1: πρωτεύον μοντέλο ---
    try:
        return _call_one_model(client, MODEL_PRIMARY, prompt_text, config)
    except Exception as e:
        print(f"      ↪️  Το {MODEL_PRIMARY} δεν τα κατάφερε — δοκιμάζω το "
              f"εφεδρικό {MODEL_FALLBACK}")

    # --- Προσπάθεια 2: εφεδρικό μοντέλο ---
    return _call_one_model(client, MODEL_FALLBACK, prompt_text, config)


def select_top_articles(client, category: str, articles: list) -> list:
    """Ρωτάει το Gemini ποια είναι τα TOP_PER_CATEGORY καλύτερα άρθρα."""
    if len(articles) <= TOP_PER_CATEGORY:
        return articles  # αν είναι λίγα, τα κρατάμε όλα

    # Φτιάχνουμε αριθμημένη λίστα τίτλων για να διαλέξει
    listing = "\n".join(
        f"{i+1}. {a['title']} ({a['source']})"
        for i, a in enumerate(articles)
    )
    prompt_text = P.SELECTION_PROMPT_TEMPLATE.format(
        count=len(articles),
        category=category,
        articles_list=listing,
        top_n=TOP_PER_CATEGORY,
    )

    try:
        answer = ask_gemini(client, prompt_text)
        # Διαβάζουμε τους αριθμούς που μας έδωσε (π.χ. "2, 7, 12")
        chosen_indices = []
        for token in answer.replace("\n", ",").split(","):
            token = token.strip()
            if token.isdigit():
                idx = int(token) - 1
                if 0 <= idx < len(articles):
                    chosen_indices.append(idx)
        chosen = [articles[i] for i in chosen_indices[:TOP_PER_CATEGORY]]
        # Αν κάτι πήγε στραβά και δεν διάλεξε τίποτα, παίρνουμε τα πρώτα
        return chosen if chosen else articles[:TOP_PER_CATEGORY]
    except Exception as e:
        print(f"   ⚠️  Πρόβλημα στην επιλογή για {category}: {e}")
        return articles[:TOP_PER_CATEGORY]


def analyze_article(client, category: str, article: dict) -> dict:
    """Ζητάει από το Gemini την πλήρη ανάλυση ενός άρθρου."""
    prompt_text = P.get_article_prompt(
        category=category,
        title=article["title"],
        source=article["source"],
        url=article["url"],
        content=article["content"],
    )
    analysis_raw = ask_gemini(client, prompt_text, system_text=P.SYSTEM_PROMPT)

    article["analysis_md"] = analysis_raw          # για το .md (Obsidian)
    article["analysis_html"] = _to_html(analysis_raw)  # για την ιστοσελίδα
    return article


def _to_html(text: str) -> str:
    """
    Μετατρέπει το κείμενο της ανάλυσης σε απλό HTML:
    - γραμμές που ξεκινούν με εικονίδιο-τίτλο γίνονται έντονοι μικρο-τίτλοι
    - οι υπόλοιπες γίνονται παράγραφοι
    """
    import html as html_lib
    label_markers = ("🔗", "🏛", "📖", "🌍", "🔮", "💡", "🎓", "🤔", "▸", "①", "②", "③")
    out = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        safe = html_lib.escape(line)
        if line.startswith(label_markers):
            out.append(f'<span class="block-label">{safe}</span>')
        else:
            out.append(f"<p>{safe}</p>")
    return "\n".join(out)


# =============================================================================
# ΜΗΧΑΝΗ 4 — Ο ΤΑΧΥΔΡΟΜΟΣ (Telegram)
# Δουλειά: στέλνει το σύντομο μήνυμα με τον σύνδεσμο της σελίδας
# =============================================================================

def send_telegram(report_data: dict, page_url: str):
    """Στέλνει σύντομο μήνυμα στο Telegram με περιλήψεις + link στη σελίδα."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN_NEWS_AGENT")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID_NEWS_AGENT")
    if not token or not chat_id:
        print("   ⚠️  Λείπουν τα Telegram secrets — παραλείπω την αποστολή.")
        return

    from builder import CATEGORY_LABELS
    today = datetime.date.today()

    # Χτίζουμε ένα σύντομο, καθαρό μήνυμα
    lines = [f"📰 *Πρωινό Δελτίο Ανάλυσης*", ""]
    for category, articles in report_data.items():
        if not articles:
            continue
        label, icon = CATEGORY_LABELS.get(category, (category, "•"))
        lines.append(f"{icon} *{label}*")
        for art in articles:
            lines.append(f"• {art['title']}")
        lines.append("")
    lines.append(f"👉 [Διάβασε την πλήρη ανάλυση εδώ]({page_url})")
    message = "\n".join(lines)

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, json={
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
        "disable_web_page_preview": False,
    })
    if resp.status_code == 200:
        print("   ✅ Το μήνυμα στάλθηκε στο Telegram!")
    else:
        print(f"   ⚠️  Σφάλμα Telegram: {resp.status_code} — {resp.text[:200]}")


# =============================================================================
# ΤΟ ΑΦΕΝΤΙΚΟ — βάζει όλες τις μηχανές σε σειρά
# =============================================================================

def run():
    import builder

    today = datetime.date.today()
    print(f"🚀 Ξεκινάω το report για {today.isoformat()}\n")

    client = make_gemini_client()
    report_data = {}

    # Για κάθε κατηγορία: μάζεψε → καθάρισε → διάλεξε → ανάλυσε
    for category in FEEDS.keys():
        print(f"📂 {category}")
        raw = collect_articles(category)
        clean = clean_articles(raw)
        print(f"   μάζεψα {len(raw)} → καθάρισα σε {len(clean)}")

        if not clean:
            report_data[category] = []
            continue

        top = select_top_articles(client, category, clean)
        print(f"   διάλεξα {len(top)} top")

        analyzed = []
        for art in top:
            try:
                analyzed.append(analyze_article(client, category, art))
                time.sleep(5)  # παύση 5s → μένουμε κάτω από 15 αιτήματα/λεπτό
            except Exception as e:
                print(f"   ⚠️  Αποτυχία ανάλυσης: {e}")
        report_data[category] = analyzed
        print(f"   ✅ ανέλυσα {len(analyzed)}\n")

    # --- Φτιάχνουμε τα αρχεία ---
    html_page = builder.build_html(report_data, today)
    md_file = builder.build_markdown(report_data, today)

    # Σώζουμε την HTML σελίδα στον φάκελο docs/ (από εκεί τη σερβίρει το GitHub Pages)
    os.makedirs("docs", exist_ok=True)
    html_filename = f"docs/{today.isoformat()}.html"
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_page)
    # Φτιάχνουμε και ένα index.html που δείχνει πάντα το σημερινό
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html_page)
    print(f"📄 Έσωσα τη σελίδα: {html_filename}")

    # Σώζουμε το .md (για Obsidian αργότερα)
    os.makedirs("reports", exist_ok=True)
    md_filename = f"reports/{today.isoformat()}.md"
    with open(md_filename, "w", encoding="utf-8") as f:
        f.write(md_file)
    print(f"📝 Έσωσα το markdown: {md_filename}")

    # --- Στέλνουμε στο Telegram ---
    # Το page_url θα το ρυθμίσουμε με το πραγματικό GitHub Pages URL σου
    page_url = os.environ.get("PAGES_URL", "")
    if page_url:
        full_url = f"{page_url}/{today.isoformat()}.html"
    else:
        full_url = "(το URL της σελίδας θα μπει μόλις ενεργοποιήσουμε το GitHub Pages)"
    send_telegram(report_data, full_url)

    print("\n🎉 Ολοκληρώθηκε!")


if __name__ == "__main__":
    run()
