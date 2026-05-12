"""
AUTOSCONTI.CH — Scraper per Promozioni Auto Svizzera
======================================================

Questo script raccoglie automaticamente le promozioni ufficiali dai siti
degli importatori svizzeri (Renault, Volkswagen/AMAG, Toyota).

Output: file JSON usabile direttamente dalla dashboard HTML.

REQUISITI: Python 3.8+
DIPENDENZE: requests, beautifulsoup4, playwright (per siti con JavaScript)
"""

import json
import re
import time
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup


# ============================================================
# CONFIGURAZIONE
# ============================================================

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept-Language": "de-CH,de;q=0.9,it;q=0.8,en;q=0.7",
}

OUTPUT_FILE = Path(__file__).parent / "deals_database.json"


# ============================================================
# SCRAPER RENAULT
# ============================================================

def scrape_renault():
    """
    Scarica le offerte ufficiali Renault dal sito svizzero.
    URL: https://de.renault.ch/angebote.html
    """
    print("🇫🇷 Scraping Renault Svizzera...")
    url = "https://de.renault.ch/angebote.html"

    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"   ❌ Errore: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(separator="\n", strip=True)

    # Estrae le campagne principali con regex
    deals = {
        "sourceUrl": url,
        "lastVerified": datetime.now().strftime("%d.%m.%Y"),
        "validity": "Da rilevare automaticamente",
        "models": {}
    }

    # Cerca le date di validità campagna
    validity_match = re.search(
        r"Vertragsabschluss\s+vom\s+(\d{2}\.\d{2}\.\d{4})\s+bis\s+(\d{2}\.\d{2}\.\d{4})",
        text
    )
    if validity_match:
        deals["validity"] = f"{validity_match.group(1)} — {validity_match.group(2)}"

    # Cerca i modelli con prezzi
    model_pattern = re.compile(
        r"(TWINGO|RENAULT 5|NEUER CLIO|RENAULT 4|MEGANE|CAPTUR|SYMBIOZ|SCENIC|AUSTRAL|RAFALE|ESPACE)"
        r".*?Preis ab CHF\s*([\d'\s]+)",
        re.DOTALL
    )

    for match in model_pattern.finditer(text):
        model_raw = match.group(1).strip()
        price_str = match.group(2).replace("'", "").replace(" ", "")
        try:
            price = int(price_str)
        except ValueError:
            continue

        # Normalizza nome modello
        model_name = model_raw.replace("NEUER ", "").replace("RENAULT ", "Renault ").title()
        if model_name == "Twingo": model_name = "Twingo"
        elif model_name == "Clio": model_name = "Clio"

        # Verifica se modello è escluso da qualche promo
        excluded_from_4yr = model_raw in ["NEUER CLIO", "TWINGO"]

        model_deals = []

        # Promo 4 anni garanzia (se applicabile)
        if not excluded_from_4yr:
            model_deals.append({
                "tag": "PROMO",
                "tagClass": "bonus",
                "title": "4 anni garanzia + manutenzione GRATIS",
                "value": "GRATIS",
                "desc": "4 anni di garanzia estesa + pacchetto manutenzione Medium incluso.",
                "fineprint": f"Contratto entro {deals['validity'].split(' — ')[1] if ' — ' in deals['validity'] else 'fine campagna'}."
            })
        else:
            model_deals.append({
                "tag": "EXCLUDED",
                "tagClass": "excluded-tag",
                "title": "❌ NON inclusa: 4 anni garanzia + manutenzione",
                "value": "—",
                "desc": f"{model_name} è ESCLUSA dalla promo 4 anni garanzia.",
                "excluded": True
            })

        # Leasing
        if "E-Tech electric" in text or "elektroautos" in model_raw.lower():
            model_deals.append({
                "tag": "0% LEASING",
                "tagClass": "bonus",
                "title": "Leasing 0% E-Tech electric",
                "value": "0%",
                "isRate": True,
                "desc": "0% TAEG con manutenzione e assicurazione incluse.",
                "fineprint": "Durata 48 mesi, 10'000 km/anno."
            })
        else:
            model_deals.append({
                "tag": "LEASING",
                "tagClass": "leasing",
                "title": "Leasing 2,99% Plus",
                "value": "2.99%",
                "isRate": True,
                "desc": "Tasso 2,99% (TAEG 3,03%) tramite Mobilize Financial Services.",
                "fineprint": "Durata 12-60 mesi, include assicurazione rate."
            })

        deals["models"][model_name] = {
            "listPrice": price,
            "deals": model_deals
        }
        print(f"   ✓ {model_name}: CHF {price:,}".replace(",", "'"))

    return deals


# ============================================================
# SCRAPER TOYOTA
# ============================================================

def scrape_toyota():
    """
    Scarica le offerte Toyota Svizzera.
    URL: https://de.toyota.ch/toyota-angebote
    """
    print("🇯🇵 Scraping Toyota Svizzera...")
    url = "https://de.toyota.ch/toyota-angebote"

    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"   ❌ Errore: {e}")
        return None

    soup = BeautifulSoup(response.text, "html.parser")
    text = soup.get_text(separator="\n", strip=True)

    deals = {
        "sourceUrl": url,
        "lastVerified": datetime.now().strftime("%d.%m.%Y"),
        "validity": "01.05.2026 — 30.06.2026",
        "models": {}
    }

    # Pattern Toyota: "Promotion title: <Modello>" seguito da "CHF X'XXX.– Prämie"
    pattern = re.compile(
        r"Promotion title:\s*([^\n]+?)\s*\n.*?CHF\s*([\d']+)\.?[–\-]*\s*Prämie.*?"
        r"From\s+CHF\s+([\d',\.]+)",
        re.DOTALL
    )

    for match in pattern.finditer(text):
        model_name = match.group(1).strip()
        bonus_str = match.group(2).replace("'", "")
        price_str = match.group(3).replace("'", "").replace(",", "").split(".")[0]

        try:
            bonus = int(bonus_str)
            price = int(price_str)
        except ValueError:
            continue

        # Pulisce nome modello
        model_name = model_name.replace("Hybrid", "").replace("Plug-in", "").strip()
        if "Yaris Cross" in model_name: model_name = "Yaris Cross"
        elif "Yaris" in model_name and "Cross" not in model_name: model_name = "Yaris"
        elif "Corolla Cross" in model_name: model_name = "Corolla Cross"
        elif "Corolla" in model_name: model_name = "Corolla"
        elif "C-HR" in model_name: model_name = "C-HR"
        elif "Aygo" in model_name: model_name = "Aygo X"
        elif "RAV4" in model_name: model_name = "RAV4"
        elif "bZ4X" in model_name: model_name = "bZ4X"
        elif "Prius" in model_name: model_name = "Prius"

        # Determina se è BEV/PHEV (leasing 0%)
        is_electric = any(k in match.group(0) for k in ["bZ4X", "Plug-in", "Electric", "PHEV"])

        model_deals = [{
            "tag": "PRÄMIE",
            "tagClass": "bonus",
            "title": f"Premio {model_name}",
            "value": f"CHF {bonus:,}".replace(",", "'"),
            "desc": f"Bonus diretto CHF {bonus:,} sull'acquisto.".replace(",", "'"),
            "fineprint": "Validità fino al 31.12.2026."
        }]

        if is_electric:
            model_deals.append({
                "tag": "0% LEASING",
                "tagClass": "bonus",
                "title": "Leasing 0% BEV/PHEV",
                "value": "0%",
                "isRate": True,
                "desc": "Toyota offre 0% TAEG su tutti i BEV e PHEV senza pacchetti aggiuntivi.",
                "fineprint": "Contratti dal 01.05 al 30.06.2026."
            })
        else:
            model_deals.append({
                "tag": "LEASING",
                "tagClass": "leasing",
                "title": "Leasing 1,99% (con pacchetti)",
                "value": "1.99%",
                "isRate": True,
                "desc": "Tasso 1,99% con Service Pack + Toyota Protect, durate ≤36 mesi.",
                "fineprint": "Senza pacchetti: 2,99% (≤48 mesi)."
            })

        model_deals.append({
            "tag": "GARANZIA",
            "tagClass": "flotta",
            "title": "Toyota Relax — 10 anni garanzia",
            "value": "10 anni",
            "desc": "Garanzia 10 anni o 185'000 km attivata ad ogni service ufficiale.",
            "fineprint": "Valida per tutti i Toyota dal 1° immatricolazione."
        })

        deals["models"][model_name] = {
            "listPrice": price,
            "deals": model_deals
        }
        print(f"   ✓ {model_name}: CHF {price:,} | Bonus CHF {bonus:,}".replace(",", "'"))

    return deals


# ============================================================
# SCRAPER VOLKSWAGEN (AMAG)
# ============================================================

def scrape_volkswagen():
    """
    Per VW serve AMAG Leasing perché VW.ch reindirizza ad amag.
    URL: https://www.amag-leasing.ch/de/amag-leasing-promotion.html

    NOTA: AMAG usa JavaScript pesante. Per uno scraping robusto serve
    Playwright. Qui usiamo requests come fallback (può essere parziale).
    """
    print("🇩🇪 Scraping Volkswagen via AMAG...")
    url = "https://www.amag-leasing.ch/de/amag-leasing-promotion.html"

    try:
        response = requests.get(url, headers=HEADERS, timeout=20)
        response.raise_for_status()
        text = BeautifulSoup(response.text, "html.parser").get_text(separator="\n")
    except requests.RequestException as e:
        print(f"   ⚠️  Errore richiesta: {e}")
        print(f"   → Suggerimento: per AMAG usare playwright (vedi commenti)")
        return None

    deals = {
        "sourceUrl": url,
        "lastVerified": datetime.now().strftime("%d.%m.%Y"),
        "validity": "Fino al 30.06.2026",
        "models": {}
    }

    # Cerca tassi specifici per modello
    rate_pattern = re.compile(
        r"(Volkswagen\s+ID\.\s*\d|ID\s*\.\s*Buzz|Golf|Polo|Tiguan)\s*,?\s*ab\s*([\d\.]+)\s*%",
        re.IGNORECASE
    )

    for match in rate_pattern.finditer(text):
        model = match.group(1).strip().replace("Volkswagen ", "").replace(" ", "")
        rate = match.group(2)

        deals["models"][model] = {
            "listPrice": 0,  # Da arricchire con altra fonte
            "deals": [{
                "tag": f"{rate}% LEASING",
                "tagClass": "bonus" if float(rate) < 1 else "leasing",
                "title": f"LeasingPLUS Go {model}",
                "value": f"{rate}%",
                "isRate": True,
                "desc": f"Tasso AMAG Leasing {rate}% effettivo annuo.",
                "fineprint": "Richiede LeasingPLUS Go + Care. Validità fino al 30.06.2026."
            }]
        }
        print(f"   ✓ {model}: tasso {rate}%")

    return deals


# ============================================================
# MAIN
# ============================================================

def main():
    print("=" * 60)
    print("  AUTOSCONTI.CH — Scraper Promozioni Auto Svizzera")
    print(f"  Esecuzione: {datetime.now().strftime('%d.%m.%Y %H:%M')}")
    print("=" * 60)

    database = {}

    # Esegui scraper con pausa tra le richieste (gentile coi server)
    for brand_name, scraper_func in [
        ("Renault", scrape_renault),
        ("Toyota", scrape_toyota),
        ("Volkswagen", scrape_volkswagen),
    ]:
        result = scraper_func()
        if result and result.get("models"):
            database[brand_name] = result
        time.sleep(2)  # Pausa di 2 secondi tra i siti

    # Salva il risultato
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(database, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 60)
    print(f"✓ Database aggiornato: {OUTPUT_FILE}")
    print(f"✓ Marche raccolte: {len(database)}")
    total_models = sum(len(b.get("models", {})) for b in database.values())
    print(f"✓ Modelli totali: {total_models}")
    print("=" * 60)


if __name__ == "__main__":
    main()
