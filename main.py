# =============================================================================
# main.py — Το «αφεντικό» που τρέχει όλη τη διαδικασία
# =============================================================================
# Η ροή: Συλλέκτης → Καθαριστής → Αναλυτής (Gemini) → Ταχυδρόμος (Telegram)
# =============================================================================

# --- Δανειζόμαστε έτοιμα εργαλεία (libraries) ---
import os               # για να διαβάζουμε τα "secrets" (κλειδιά)
import re               # για regex (καθαρισμός markdown asterisks)
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
MODEL_PRIMARY  = "gemini-2.5-flash"       # σταθερό, οικονομικό (~$1.50/μήνα)
MODEL_FALLBACK = "gemini-2.5-flash-lite"  # εφεδρικό, ελάχιστο κόστος

# Τιμές για υπολογισμό κόστους (USD ανά 1 εκατομμύριο tokens)
MODEL_PRICES = {
    "gemini-3.5-flash":      {"input": 1.50, "output": 9.00},
    "gemini-2.5-flash":      {"input": 0.30, "output": 2.50},
    "gemini-2.5-flash-lite": {"input": 0.10, "output": 0.40},
}

# Όνομα του secret με το κλειδί (όπως το έβαλες στο GitHub)
API_KEY_NAME = "GEMINI_API_KEY_NEWS_AGENT"

# "Γραβάτα" — λέμε στις ειδησεογραφικές σελίδες ότι είμαστε κανονικός browser.
USER_AGENT = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
              "AppleWebKit/537.36 (KHTML, like Gecko) "
              "Chrome/120.0.0.0 Safari/537.36")

# Μετρητής tokens για υπολογισμό κόστους
_token_usage = {"input": 0, "output": 0, "model_calls": {}}


# =============================================================================
# ΜΗΧΑΝΗ 1 — Ο ΣΥΛΛΕΚΤΗΣ
# =============================================================================

def collect_articles(category: str) -> list:
    articles = []
    feed_urls = FEEDS[category]

    for url in feed_urls:
        try:
            parsed = feedparser.parse(url, agent=USER_AGENT)
            source_name = parsed.feed.get("title", url)
            for entry in parsed.entries[:ARTICLES_PER_FEED]:
                articles.append({
                    "title": entry.get("title", "Χωρίς τίτλο"),
                    "url": entry.get("link", ""),
                    "source": source_name,
                    "content": entry.get("summary", ""),
                })
        except Exception as e:
            print(f"   ⚠️  Πρόβλημα με πηγή {url}: {e}")
            continue

    return articles


# =============================================================================
# ΜΗΧΑΝΗ 2 — Ο ΚΑΘΑΡΙΣΤΗΣ
# =============================================================================

def clean_articles(articles: list) -> list:
    seen_titles = set()
    cleaned = []

    for article in articles:
        title = article["title"].strip()
        if not title or not article["url"]:
            continue
        fingerprint = title.lower()[:60]
        if fingerprint in seen_titles:
            continue
        seen_titles.add(fingerprint)
        cleaned.append(article)

    return cleaned


# =============================================================================
# ΜΗΧΑΝΗ 3 — Ο ΑΝΑΛΥΤΗΣ (Gemini)
# =============================================================================

def make_gemini_client():
    api_key = os.environ.get(API_KEY_NAME)
    if not api_key:
        raise RuntimeError(f"Δεν βρέθηκε το κλειδί '{API_KEY_NAME}'.")
    return genai.Client(api_key=api_key)


def _track_tokens(response, model_name: str):
    """Καταγράφει tokens από κάθε κλήση για υπολογισμό κόστους."""
    try:
        meta = response.usage_metadata
        inp = getattr(meta, "prompt_token_count", 0) or 0
        out = getattr(meta, "candidates_token_count", 0) or 0
        _token_usage["input"]  += inp
        _token_usage["output"] += out
        calls = _token_usage["model_calls"]
        if model_name not in calls:
            calls[model_name] = {"input": 0, "output": 0}
        calls[model_name]["input"]  += inp
        calls[model_name]["output"] += out
    except Exception:
        pass  # αν δεν έχει metadata, απλώς συνεχίζουμε


def calculate_cost() -> tuple[float, str]:
    """Υπολογίζει το συνολικό κόστος από τα καταγεγραμμένα tokens."""
    total_cost = 0.0
    for model_name, usage in _token_usage["model_calls"].items():
        prices = MODEL_PRICES.get(model_name, {"input": 0.30, "output": 2.50})
        cost = (usage["input"] / 1_000_000 * prices["input"] +
                usage["output"] / 1_000_000 * prices["output"])
        total_cost += cost

    total_in  = _token_usage["input"]
    total_out = _token_usage["output"]
    summary = (f"${total_cost:.4f} "
               f"({total_in:,} input + {total_out:,} output tokens)")
    return total_cost, summary


def _call_one_model(client, model_name, prompt_text, config):
    """Καλεί ένα μοντέλο με backoff 2s, 4s — μέγιστο 3 προσπάθειες."""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt_text,
                config=config,
            )
            _track_tokens(response, model_name)
            return response.text
        except Exception as e:
            msg = str(e)
            is_retryable = any(code in msg for code in
                               ("503", "429", "UNAVAILABLE", "RESOURCE_EXHAUSTED",
                                "500", "504"))
            if is_retryable and attempt < max_attempts - 1:
                wait = 2 * (attempt + 1)
                print(f"      ⏳ {model_name}: γεμάτο — περιμένω {wait}s "
                      f"({attempt + 1}/{max_attempts})...")
                time.sleep(wait)
                continue
            raise


def ask_gemini(client, prompt_text: str, system_text: str = "") -> str:
    """Πρωτεύον μοντέλο με backoff, fallback στο εφεδρικό αν χρειαστεί."""
    from google.genai import types

    config = None
    if system_text:
        config = types.GenerateContentConfig(system_instruction=system_text)

    try:
        return _call_one_model(client, MODEL_PRIMARY, prompt_text, config)
    except Exception:
        print(f"      ↪️  Το {MODEL_PRIMARY} δεν τα κατάφερε — "
              f"δοκιμάζω το εφεδρικό {MODEL_FALLBACK}")

    return _call_one_model(client, MODEL_FALLBACK, prompt_text, config)


def select_top_articles(client, category: str, articles: list) -> list:
    """Επιλογή top άρθρων με βάση αξιοπιστία πηγής + ποικιλία (χωρίς API call)."""
    if len(articles) <= TOP_PER_CATEGORY:
        return articles

    trusted = ("reuters", "associated press", " ap ", "afp", "bloomberg",
               "financial times", "economist", "wall street journal")

    def score(article):
        src = article["source"].lower()
        return 1 if any(t in src for t in trusted) else 0

    ranked = sorted(articles, key=score, reverse=True)
    chosen = []
    used_sources = []
    for art in ranked:
        src = art["source"]
        if used_sources.count(src) < 1:
            chosen.append(art)
            used_sources.append(src)
        if len(chosen) >= TOP_PER_CATEGORY:
            break

    if len(chosen) < TOP_PER_CATEGORY:
        for art in ranked:
            if art not in chosen:
                chosen.append(art)
            if len(chosen) >= TOP_PER_CATEGORY:
                break

    return chosen[:TOP_PER_CATEGORY]


def _to_html(text: str) -> str:
    """
    Μετατρέπει το κείμενο της ανάλυσης σε καθαρό HTML:
    - **bold** → <strong>bold</strong>
    - *italic* → <em>italic</em>
    - γραμμές με εικονίδια-τίτλους → block-label (έντονα)
    - ①②③ → στυλιζαρισμένες παράγραφοι με indent
    - αφαιρεί τυχαία * που δεν είναι markup
    """
    import html as html_lib

    label_markers = ("🔗", "🏛", "📖", "🌍", "🔮", "💡", "🎓", "🤔", "▸")
    numbered      = ("①", "②", "③")

    out = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue

        # 1. Escape HTML special chars πρώτα
        safe = html_lib.escape(line)

        # 2. **bold** → <strong>
        safe = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', safe)

        # 3. *italic* — μόνο μεμονωμένο * (δεν αγγίζει ήδη-μετατραπέντα)
        safe = re.sub(r'(?<!\*)\*(?!\*)([^*]+?)(?<!\*)\*(?!\*)',
                      r'<em>\1</em>', safe)

        # 4. Αφαίρεσε τυχαία * που έμειναν
        safe = re.sub(r'\*', '', safe)

        # 5. Κατηγοριοποίηση
        if line.startswith(label_markers):
            out.append(f'<span class="block-label">{safe}</span>')
        elif line.startswith(numbered):
            out.append(f'<p class="numbered-point">{safe}</p>')
        else:
            out.append(f"<p>{safe}</p>")

    return "\n".join(out)


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

    article["analysis_md"]   = analysis_raw
    article["analysis_html"] = _to_html(analysis_raw)
    return article


# =============================================================================
# ΜΗΧΑΝΗ 4 — Ο ΤΑΧΥΔΡΟΜΟΣ (Telegram)
# =============================================================================

def send_telegram(report_data: dict, page_url: str, cost_summary: str = ""):
    """
    Στέλνει στο Telegram:
    - Εισαγωγικό μήνυμα με ημερομηνία + κόστος report
    - Ένα link ανά κατηγορία που πάει κατευθείαν στη σωστή ενότητα
    """
    token   = os.environ.get("TELEGRAM_BOT_TOKEN_NEWS_AGENT")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID_NEWS_AGENT")
    if not token or not chat_id:
        print("   ⚠️  Λείπουν τα Telegram secrets — παραλείπω την αποστολή.")
        return

    from builder import CATEGORY_LABELS
    today = datetime.date.today()

    months = ["Ιανουαρίου","Φεβρουαρίου","Μαρτίου","Απριλίου","Μαΐου",
              "Ιουνίου","Ιουλίου","Αυγούστου","Σεπτεμβρίου","Οκτωβρίου",
              "Νοεμβρίου","Δεκεμβρίου"]
    date_str = f"{today.day} {months[today.month-1]} {today.year}"

    def send_msg(text):
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        resp = requests.post(url, json={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "Markdown",
            "disable_web_page_preview": True,
        })
        if resp.status_code != 200:
            print(f"   ⚠️  Σφάλμα Telegram: {resp.status_code} — {resp.text[:100]}")

    # Μήνυμα 1: Εισαγωγή + κόστος
    cost_line = f"\n💰 Κόστος report: {cost_summary}" if cost_summary else ""
    send_msg(
        f"📰 *Πρωινό Δελτίο Ανάλυσης*\n"
        f"_{date_str}_{cost_line}\n\n"
        f"Πάτα σε κάθε θεματική για να ανοίξεις κατευθείαν την ανάλυσή της 👇"
    )
    time.sleep(0.5)

    # Μήνυμα 2: Links ανά κατηγορία
    lines = []
    for category, articles in report_data.items():
        if not articles:
            continue
        label, icon = CATEGORY_LABELS.get(category, (category, "•"))
        count  = len(articles)
        anchor = category.lower().replace("_", "-")

        if page_url:
            link = f"{page_url}/{today.isoformat()}.html#{anchor}"
            lines.append(f"{icon} [{label} — {count} αναλύσεις]({link})")
        else:
            lines.append(f"{icon} *{label}* — {count} αναλύσεις")

    send_msg("\n\n".join(lines))
    print("   ✅ Το μήνυμα στάλθηκε στο Telegram!")


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
        raw   = collect_articles(category)
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
                time.sleep(2)
            except Exception as e:
                print(f"   ⚠️  Αποτυχία ανάλυσης: {e}")
        report_data[category] = analyzed
        print(f"   ✅ ανέλυσα {len(analyzed)}\n")

    # --- Υπολογισμός κόστους ---
    total_cost, cost_summary = calculate_cost()
    print(f"💰 Κόστος σημερινού report: {cost_summary}")

    # --- Φτιάχνουμε τα αρχεία ---
    html_page = builder.build_html(report_data, today, cost_summary)
    md_file   = builder.build_markdown(report_data, today, cost_summary)

    os.makedirs("docs", exist_ok=True)
    html_filename = f"docs/{today.isoformat()}.html"
    with open(html_filename, "w", encoding="utf-8") as f:
        f.write(html_page)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html_page)
    print(f"📄 Έσωσα τη σελίδα: {html_filename}")

    os.makedirs("reports", exist_ok=True)
    md_filename = f"reports/{today.isoformat()}.md"
    with open(md_filename, "w", encoding="utf-8") as f:
        f.write(md_file)
    print(f"📝 Έσωσα το markdown: {md_filename}")

    # --- Στέλνουμε στο Telegram ---
    page_url = os.environ.get("PAGES_URL", "")
    if page_url:
        full_url = f"{page_url}/{today.isoformat()}.html"
    else:
        full_url = ""
    send_telegram(report_data, full_url, cost_summary)

    print("\n🎉 Ολοκληρώθηκε!")


if __name__ == "__main__":
    run()
