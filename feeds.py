# =============================================================================
# feeds.py — Λίστα πηγών ειδήσεων ανά κατηγορία
# =============================================================================
# Τι κάνει αυτό το αρχείο:
#   Ορίζει από πού μαζεύουμε ειδήσεις για κάθε κατηγορία.
#   Κάθε κατηγορία έχει πολλές πηγές (RSS feeds) ώστε να έχουμε
#   ποικιλία και να μην εξαρτόμαστε από μία μόνο εφημερίδα.
#
# Πώς να το τροποποιήσεις (χωρίς να ξέρεις κώδικα):
#   - Για να ΠΡΟΣΘΕΣΕΙΣ πηγή: πρόσθεσε μια γραμμή με το URL του RSS feed
#   - Για να ΑΦΑΙΡΕΣΕΙΣ πηγή: βάλε # μπροστά στη γραμμή (την "σβήνει")
#   - Μην αλλάξεις τα ονόματα κατηγοριών (POLITICS, AI κ.λπ.) —
#     τα χρησιμοποιεί ο υπόλοιπος κώδικας
# =============================================================================

FEEDS = {

    "POLITICS": [
        # Διεθνής πολιτική — wire services & αναλυτικά media
        "https://feeds.reuters.com/Reuters/PoliticsNews",
        "https://rss.nytimes.com/services/xml/rss/nyt/Politics.xml",
        "https://feeds.bbci.co.uk/news/politics/rss.xml",
        "https://www.politico.com/rss/politicopicks.xml",
        "https://thehill.com/rss/syndicator/19109",
    ],

    "GEOPOLITICS_DIPLOMACY": [
        # Γεωπολιτική & διπλωματία — εστίαση σε παγκόσμια ισορροπία ισχύος
        "https://feeds.reuters.com/Reuters/worldNews",
        "https://foreignpolicy.com/feed/",
        "https://www.aljazeera.com/xml/rss/all.xml",
        "https://www.france24.com/en/rss",
        "https://www.chathamhouse.org/rss.xml",
    ],

    "ECONOMICS_FINANCE": [
        # Οικονομία & χρηματοοικονομικά — νούμερα που έχουν νόημα
        "https://feeds.reuters.com/reuters/businessNews",
        "https://feeds.bloomberg.com/markets/news.rss",
        "https://www.ft.com/rss/home",
        "https://www.economist.com/finance-and-economics/rss.xml",
        "https://feeds.marketwatch.com/marketwatch/topstories/",
    ],

    "INTL_BUSINESS_STRATEGY": [
        # International Business / Strategy & Innovation — το "σχολικό" σου υλικό
        "https://hbr.org/feed",
        "https://sloanreview.mit.edu/feed/",
        "https://feeds.reuters.com/reuters/businessNews",
        "https://www.economist.com/business/rss.xml",
        "https://www.bcg.com/rss/perspectives",
    ],

    "AI": [
        # Τεχνητή νοημοσύνη — ουσία vs hype
        "https://techcrunch.com/feed/",
        "https://www.theverge.com/rss/ai-artificial-intelligence/index.xml",
        "https://feeds.technologyreview.com/feed",
        "https://arstechnica.com/feed/",
        "https://venturebeat.com/category/ai/feed/",
    ],

    "STOCK_MARKETS": [
        # Χρηματιστήρια — ανάλυση κινήσεων, όχι επενδυτικές συμβουλές
        "https://feeds.reuters.com/reuters/businessNews",
        "https://feeds.bloomberg.com/markets/news.rss",
        "https://feeds.marketwatch.com/marketwatch/topstories/",
        "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "https://feeds.a.dj.com/rss/WSJcomUSBusiness.xml",
    ],

    "PHILOSOPHICAL_OPINIONS": [
        # Φιλοσοφία & απόψεις — για να σκέφτεσαι, όχι να απαντάς
        "https://aeon.co/feed.rss",
        "https://bigthink.com/feed/",
        "https://www.project-syndicate.org/rss",
        "https://www.nytimes.com/svc/collections/v1/publish/https://www.nytimes.com/section/opinion/rss.xml",
        "https://iai.tv/feed",
    ],

}

# =============================================================================
# Πόσα άρθρα μαζεύουμε ανά πηγή;
# Βάζουμε 10 — το Gemini θα διαλέξει τα 3 καλύτερα από όλα.
# Αν θες περισσότερη ποικιλία, ανέβασε τον αριθμό (π.χ. 15).
# =============================================================================
ARTICLES_PER_FEED = 10

# =============================================================================
# Πόσα TOP άρθρα θέλουμε ανά κατηγορία στο τελικό report;
# =============================================================================
TOP_PER_CATEGORY = 3
