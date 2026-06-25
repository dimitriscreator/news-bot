# 📰 Daily News Intelligence Bot

Αυτόματο σύστημα που κάθε πρωί στις 07:00:
1. Μαζεύει ειδήσεις από RSS feeds (7 κατηγορίες)
2. Επιλέγει & αναλύει τα top 3 ανά κατηγορία με Gemini
3. Φτιάχνει μια όμορφη HTML σελίδα με την πλήρη ανάλυση
4. Στέλνει σύντομο μήνυμα στο Telegram με σύνδεσμο προς τη σελίδα
5. Σώζει .md αρχείο για ενσωμάτωση σε Obsidian

## Δομή αρχείων

| Αρχείο | Δουλειά |
|--------|---------|
| `feeds.py` | Λίστα πηγών RSS ανά κατηγορία. **Άλλαξε εδώ τις πηγές.** |
| `prompt.py` | Οι οδηγίες προς το Gemini. **Άλλαξε εδώ το ύφος/δομή ανάλυσης.** |
| `builder.py` | Φτιάχνει την HTML σελίδα + το .md αρχείο. **Άλλαξε εδώ την εμφάνιση.** |
| `main.py` | Το «αφεντικό» — ενώνει τα πάντα σε σειρά. |
| `requirements.txt` | Λίστα εργαλείων (libraries). |
| `.github/workflows/daily.yml` | Το χρονοδιάγραμμα (τρέχει στις 07:00). |

## Ροή

```
feeds.py → main.py (Συλλέκτης → Καθαριστής)
        → Gemini (Επιλογή → Ανάλυση)
        → builder.py (HTML + .md)
        → Telegram
```

## Secrets που χρειάζονται (στο GitHub → Settings → Secrets → Actions)

- `GEMINI_API_KEY_NEWS_AGENT`
- `TELEGRAM_BOT_TOKEN_NEWS_AGENT`
- `TELEGRAM_CHAT_ID_NEWS_AGENT`

## Variable (στο GitHub → Settings → Variables → Actions)

- `PAGES_URL` — το URL του GitHub Pages (π.χ. `https://USERNAME.github.io/news-bot`)

## Μοντέλο

Χρησιμοποιεί `gemini-3.5-flash` (δωρεάν tier). Άλλαξε το `MODEL_NAME` στο `main.py`
αν θες άλλο μοντέλο.
