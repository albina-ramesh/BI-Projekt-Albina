"""
=============================================================
  FreshMart – Schritt 3: AI-Agent mit SQL-Datenbank
  Agentische Verkaufsanalytik | FHNW Business Intelligence
  Prof. Dr. Manuel Renold | ffnlw04
=============================================================
"""

import os
from dotenv import load_dotenv
import sqlite3
import pandas as pd
from groq import Groq

# ─────────────────────────────────────────────
#  KONFIGURATION  ← hier deinen Key eintragen
# ─────────────────────────────────────────────
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
MODEL        = "llama-3.3-70b-versatile"
DB_DATEI     = "freshmart.db"

# ─────────────────────────────────────────────
#  DATENBANKVERBINDUNG
# ─────────────────────────────────────────────
def db_query(sql: str) -> str:
    """Führt eine SQL-Abfrage auf der SQLite-Datenbank aus."""
    if not os.path.exists(DB_DATEI):
        return f"❌ Datenbank '{DB_DATEI}' nicht gefunden. Bitte zuerst schritt2_datenbank.py ausführen."
    try:
        conn = sqlite3.connect(DB_DATEI)
        df   = pd.read_sql_query(sql, conn)
        conn.close()
        if df.empty:
            return "Keine Daten gefunden."
        return df.to_string(index=False)
    except Exception as e:
        return f"SQL-Fehler: {e}"

# ─────────────────────────────────────────────
#  TOOL-FUNKTIONEN (der Agent ruft diese auf)
# ─────────────────────────────────────────────

def get_gesamtuebersicht() -> str:
    """Gesamtkennzahlen von FreshMart."""
    sql = """
    SELECT
        COUNT(*)                              AS total_transaktionen,
        ROUND(SUM(umsatz_chf), 2)             AS gesamtumsatz_chf,
        ROUND(SUM(gewinn_chf), 2)             AS gesamtgewinn_chf,
        ROUND(AVG(umsatz_chf), 2)             AS avg_bon_chf,
        ROUND(SUM(gewinn_chf)/SUM(umsatz_chf)*100, 1) AS marge_pct,
        COUNT(DISTINCT filiale_id)            AS anzahl_filialen,
        COUNT(DISTINCT produkt_id)            AS anzahl_produkte
    FROM verkaeufe
    """
    return "=== FreshMart Gesamtübersicht 2024 ===\n" + db_query(sql)

def get_filialen_ranking() -> str:
    """Ranking aller Filialen nach Umsatz."""
    sql = "SELECT * FROM v_umsatz_pro_filiale"
    return "=== Filial-Ranking (SQL: v_umsatz_pro_filiale) ===\n" + db_query(sql)

def get_top10_produkte() -> str:
    """Top 10 Produkte nach Umsatz."""
    sql = "SELECT * FROM v_top_produkte LIMIT 10"
    return "=== Top 10 Produkte (SQL: v_top_produkte) ===\n" + db_query(sql)

def get_schwachste_produkte() -> str:
    """Die 10 schwächsten Produkte nach Umsatz."""
    sql = "SELECT * FROM v_top_produkte ORDER BY total_umsatz_chf ASC LIMIT 10"
    return "=== Schwächste 10 Produkte ===\n" + db_query(sql)

def get_kategorien_analyse() -> str:
    """Umsatz und Marge nach Produktkategorie."""
    sql = "SELECT * FROM v_umsatz_pro_kategorie"
    return "=== Kategorienanalyse (SQL: v_umsatz_pro_kategorie) ===\n" + db_query(sql)

def get_monatstrend() -> str:
    """Monatlicher Umsatztrend 2024."""
    sql = """
    SELECT monat, quartal, transaktionen,
           umsatz_chf, gewinn_chf
    FROM v_monatstrend
    ORDER BY CASE monat
        WHEN 'January' THEN 1 WHEN 'February' THEN 2 WHEN 'March' THEN 3
        WHEN 'April' THEN 4 WHEN 'May' THEN 5 WHEN 'June' THEN 6
        WHEN 'July' THEN 7 WHEN 'August' THEN 8 WHEN 'September' THEN 9
        WHEN 'October' THEN 10 WHEN 'November' THEN 11 WHEN 'December' THEN 12
    END
    """
    return "=== Monatstrend 2024 (SQL: v_monatstrend) ===\n" + db_query(sql)

def get_wochentag_analyse() -> str:
    """Umsatz nach Wochentag."""
    sql = """
    SELECT wochentag,
           COUNT(*) AS transaktionen,
           ROUND(SUM(umsatz_chf),2) AS umsatz_chf,
           ROUND(AVG(umsatz_chf),2) AS avg_bon_chf
    FROM verkaeufe
    GROUP BY wochentag
    ORDER BY CASE wochentag
        WHEN 'Montag' THEN 1 WHEN 'Dienstag' THEN 2 WHEN 'Mittwoch' THEN 3
        WHEN 'Donnerstag' THEN 4 WHEN 'Freitag' THEN 5
        WHEN 'Samstag' THEN 6 WHEN 'Sonntag' THEN 7
    END
    """
    return "=== Umsatz nach Wochentag ===\n" + db_query(sql)

def get_zahlungsmethoden() -> str:
    """Verteilung der Zahlungsmethoden."""
    sql = """
    SELECT zahlungsmethode,
           COUNT(*) AS anzahl,
           ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM verkaeufe),1) AS anteil_pct,
           ROUND(SUM(umsatz_chf),2) AS umsatz_chf
    FROM verkaeufe
    GROUP BY zahlungsmethode
    ORDER BY anzahl DESC
    """
    return "=== Zahlungsmethoden ===\n" + db_query(sql)

def get_quartal_vergleich() -> str:
    """Quartalsvergleich Q1-Q4."""
    sql = """
    SELECT quartal,
           COUNT(*) AS transaktionen,
           ROUND(SUM(umsatz_chf),2) AS umsatz_chf,
           ROUND(SUM(gewinn_chf),2) AS gewinn_chf,
           ROUND(SUM(gewinn_chf)/SUM(umsatz_chf)*100,1) AS marge_pct
    FROM verkaeufe
    GROUP BY quartal
    ORDER BY quartal
    """
    return "=== Quartalsvergleich 2024 ===\n" + db_query(sql)

def get_handlungsempfehlungen() -> str:
    """Analysiert alle Daten und gibt Handlungsempfehlungen."""
    # Beste/schlechteste Filiale
    beste_filiale = db_query("SELECT filialname, total_umsatz_chf FROM v_umsatz_pro_filiale LIMIT 1")
    schlechte_filiale = db_query("SELECT filialname, total_umsatz_chf FROM v_umsatz_pro_filiale ORDER BY total_umsatz_chf ASC LIMIT 1")

    # Beste Kategorie (Marge)
    beste_kat = db_query("SELECT kategorie, marge_pct FROM v_umsatz_pro_kategorie ORDER BY marge_pct DESC LIMIT 1")
    schlechte_kat = db_query("SELECT kategorie, marge_pct FROM v_umsatz_pro_kategorie ORDER BY marge_pct ASC LIMIT 1")

    # Schwächstes Produkt
    schwach = db_query("SELECT produktname, total_umsatz_chf FROM v_top_produkte ORDER BY total_umsatz_chf ASC LIMIT 1")

    # Samstag vs Sonntag
    sa_so = db_query("""
        SELECT wochentag, ROUND(SUM(umsatz_chf),2) as umsatz
        FROM verkaeufe WHERE wochentag IN ('Samstag','Sonntag')
        GROUP BY wochentag
    """)

    return f"""
=== HANDLUNGSEMPFEHLUNGEN – FreshMart 2024 ===

📊 DATENBASIS (aus SQLite-Datenbank):

Beste Filiale:       {beste_filiale}
Schwächste Filiale:  {schlechte_filiale}
Beste Kategorie:     {beste_kat}
Schwächste Kategorie:{schlechte_kat}
Schwächstes Produkt: {schwach}
Samstag vs Sonntag:  {sa_so}

✅ EMPFEHLUNGEN:
1. Best-Practice-Transfer: Erfolgskonzept der besten Filiale auf schwächere übertragen.
2. Sortimentsoptimierung: Schwächstes Produkt aus Sortiment nehmen oder Preis senken.
3. Margensteigerung: Kategorie mit höchster Marge im Regal priorisieren.
4. Wochentag-Aktion: Sonntag mit Spezialaktionen stärken.
5. Lieferantenverhandlung: Bei schwächster Kategorie Einkaufspreise neu verhandeln.
"""

# ─────────────────────────────────────────────
#  TOOL-DEFINITIONEN FÜR DEN AGENTEN
# ─────────────────────────────────────────────
TOOLS = [
    {"type":"function","function":{"name":"get_gesamtuebersicht",
     "description":"Gibt alle wichtigen Gesamtkennzahlen von FreshMart zurück (Umsatz, Gewinn, Marge, Transaktionen).",
     "parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_filialen_ranking",
     "description":"Gibt das Ranking aller FreshMart Filialen nach Umsatz zurück via SQL.",
     "parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_top10_produkte",
     "description":"Gibt die Top 10 Produkte nach Umsatz zurück via SQL.",
     "parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_schwachste_produkte",
     "description":"Gibt die 10 schwächsten Produkte nach Umsatz zurück.",
     "parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_kategorien_analyse",
     "description":"Gibt Umsatz, Gewinn und Marge nach Produktkategorie zurück via SQL.",
     "parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_monatstrend",
     "description":"Gibt den monatlichen Umsatztrend für 2024 zurück via SQL.",
     "parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_wochentag_analyse",
     "description":"Gibt die Umsatzverteilung nach Wochentag zurück via SQL.",
     "parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_zahlungsmethoden",
     "description":"Gibt die Verteilung der Zahlungsmethoden zurück.",
     "parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_quartal_vergleich",
     "description":"Gibt den Quartalsvergleich Q1 bis Q4 zurück.",
     "parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_handlungsempfehlungen",
     "description":"Analysiert alle Daten und gibt konkrete Handlungsempfehlungen zurück.",
     "parameters":{"type":"object","properties":{},"required":[]}}},
]

TOOL_MAP = {
    "get_gesamtuebersicht":     get_gesamtuebersicht,
    "get_filialen_ranking":     get_filialen_ranking,
    "get_top10_produkte":       get_top10_produkte,
    "get_schwachste_produkte":  get_schwachste_produkte,
    "get_kategorien_analyse":   get_kategorien_analyse,
    "get_monatstrend":          get_monatstrend,
    "get_wochentag_analyse":    get_wochentag_analyse,
    "get_zahlungsmethoden":     get_zahlungsmethoden,
    "get_quartal_vergleich":    get_quartal_vergleich,
    "get_handlungsempfehlungen":get_handlungsempfehlungen,
}

SYSTEM_PROMPT = """Du bist ein Business Intelligence AI-Agent für FreshMart Schweiz –
eine Schweizer Supermarkt-Kette mit 8 Filialen und 30 Produkten.

Deine Datenbasis: SQLite-Datenbank mit 10'000 Verkaufstransaktionen aus 2024.
Die Daten wurden aus einer Excel-Datei (freshmart_verkaufsdaten.xlsx) geladen.

Deine Aufgaben:
- Verkaufsdaten per SQL-Abfragen analysieren
- Filialen, Produkte und Kategorien vergleichen
- Trends und Muster erkennen (Monate, Quartale, Wochentage)
- Konkrete, datenbasierte Handlungsempfehlungen geben
- Klar und professionell auf Deutsch antworten

Nutze immer zuerst die Tools um aktuelle Daten aus der Datenbank abzurufen.
Erwähne bei Antworten welche SQL-Abfrage / welcher View verwendet wurde.
"""

# ─────────────────────────────────────────────
#  AGENTEN-LOOP
# ─────────────────────────────────────────────

def run_agent(frage: str, client: Groq, history: list) -> str:
    history.append({"role": "user", "content": frage})

    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
        tools=TOOLS,
        tool_choice="auto",
        max_tokens=1500
    )
    msg = response.choices[0].message

    if msg.tool_calls:
        history.append({"role": "assistant", "content": None, "tool_calls": [
            {"id": tc.id, "type": "function",
             "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
            for tc in msg.tool_calls
        ]})

        for tc in msg.tool_calls:
            fn = TOOL_MAP.get(tc.function.name)
            result = fn() if fn else f"Unbekanntes Tool: {tc.function.name}"
            print(f"  🔧 SQL-Tool: {tc.function.name}()")
            history.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        final = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
            max_tokens=1500
        )
        antwort = final.choices[0].message.content
    else:
        antwort = msg.content

    history.append({"role": "assistant", "content": antwort})
    return antwort

# ─────────────────────────────────────────────
#  HAUPTPROGRAMM
# ─────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  🛒  FreshMart AI-Agent – SQL + Agentische Analytik")
    print("  Business Intelligence | FHNW | ffnlw04")
    print("  Datenquelle: Excel → SQLite | 10'000 Transaktionen")
    print("=" * 60)
    print("\nBeispiel-Fragen:")
    print("  • Welches Produkt verkauft sich am besten?")
    print("  • Vergleiche alle Filialen nach Umsatz")
    print("  • Wie war Q4 im Vergleich zu Q1?")
    print("  • Welche Kategorie hat die höchste Marge?")
    print("  • Was soll ich tun um den Gewinn zu steigern?")
    print("  • Wann kaufen Kunden am meisten ein?\n")

    api_key = GROQ_API_KEY if GROQ_API_KEY != "DEIN_GROQ_API_KEY_HIER" else os.getenv("GROQ_API_KEY","")
    if not api_key:
        print("❌ Bitte GROQ_API_KEY in schritt3_agent.py eintragen!")
        return

    client  = Groq(api_key=api_key)
    history = []

    print("🤖 Agent verbindet sich mit der Datenbank...\n")
    start = run_agent(
        "Begrüsse die Geschäftsleitung von FreshMart und gib einen prägnanten "
        "Executive Summary der wichtigsten Kennzahlen 2024.",
        client, history
    )
    print(f"🤖 Agent:\n{start}\n")
    print("-" * 60)

    while True:
        try:
            frage = input("\n👤 Du: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nAuf Wiedersehen! 🛒")
            break
        if not frage:
            continue
        if frage.lower() in ("exit","quit","beenden"):
            print("Auf Wiedersehen! 🛒")
            break
        print()
        antwort = run_agent(frage, client, history)
        print(f"🤖 Agent:\n{antwort}")
        print("-" * 60)

if __name__ == "__main__":
    main()
