# 🚗 Autosconti.ch

Dashboard delle promozioni ufficiali auto in Svizzera, aggiornata automaticamente.

## 🌐 Sito live

→ **https://[tuonome].netlify.app** (modifica con il tuo URL)

## 🤖 Come funziona

Ogni notte alle 06:00 (ora svizzera) uno scraper Python visita i siti ufficiali degli importatori:

- 🇫🇷 Renault Svizzera ([renault.ch](https://de.renault.ch/angebote.html))
- 🇯🇵 Toyota Svizzera ([toyota.ch](https://de.toyota.ch/toyota-angebote))
- 🇩🇪 Volkswagen via AMAG ([amag-leasing.ch](https://www.amag-leasing.ch))

Estrae bonus, tassi leasing, premi stock e altre promozioni e li salva in `deals_database.json`. Le pagine HTML leggono questo file e si aggiornano automaticamente.

## 📁 Struttura del repository

```
├── index.html              ← Home page con le novità in primo piano
├── autosconti-ch-v2.html   ← Dashboard ricerca per marca/modello
├── scraper.py              ← Script Python che raccoglie le promo
├── deals_database.json     ← Database delle offerte (generato dallo scraper)
└── .github/workflows/
    └── scrape.yml          ← GitHub Actions: esegue lo scraper ogni notte
```

## 🛠️ Sviluppo

Per testare in locale:

```bash
pip install requests beautifulsoup4
python scraper.py
python -m http.server 8000
# Apri http://localhost:8000
```

## 📅 Aggiornamenti

Il database si aggiorna automaticamente. Per forzare un aggiornamento manuale:

1. Vai nella tab **Actions** del repository
2. Seleziona **Aggiorna sconti auto**
3. Clicca **Run workflow**

## ⚖️ Disclaimer

I dati sono raccolti dai siti ufficiali degli importatori svizzeri. Verifica sempre presso il concessionario prima di decisioni d'acquisto. Le promozioni possono cambiare in qualsiasi momento.

## 📄 Licenza

Progetto personale. I marchi citati appartengono ai rispettivi proprietari.
