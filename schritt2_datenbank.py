"""
FreshMart – Schritt 2: Excel → SQLite Datenbank
Liest die Excel-Datei und lädt die Daten in eine SQLite-Datenbank.
Erstellt dabei mehrere Tabellen (normalisiert wie ein echtes Data Warehouse).
"""

import pandas as pd
import sqlite3
import os

EXCEL_DATEI = "freshmart_verkaufsdaten.xlsx"
DB_DATEI    = "freshmart.db"

print("=" * 55)
print("  FreshMart – Daten in SQLite laden")
print("=" * 55)

if not os.path.exists(EXCEL_DATEI):
    print(f"❌ '{EXCEL_DATEI}' nicht gefunden!")
    print("   Bitte zuerst: python schritt1_daten_erstellen.py")
    exit(1)

# ── Excel einlesen ────────────────────────────────────────
print(f"\n📂 Lese '{EXCEL_DATEI}'...")
df = pd.read_excel(EXCEL_DATEI, sheet_name="Verkaufsdaten", header=1)
print(f"   {len(df):,} Datensätze geladen")

# ── Datenbank aufbauen ────────────────────────────────────
print(f"\n🗄️  Erstelle SQLite-Datenbank '{DB_DATEI}'...")
if os.path.exists(DB_DATEI):
    os.remove(DB_DATEI)

conn = sqlite3.connect(DB_DATEI)
cur  = conn.cursor()

# ── Tabelle 1: Filialen (Dimensionstabelle) ───────────────
cur.execute("""
CREATE TABLE filialen (
    filiale_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    filialname   TEXT NOT NULL UNIQUE,
    kanton       TEXT NOT NULL,
    groesse      TEXT NOT NULL,
    typ          TEXT NOT NULL
)
""")

filialen_unique = df[["Filiale","Kanton","Filialgroesse","Filialtyp"]].drop_duplicates()
for _, row in filialen_unique.iterrows():
    cur.execute(
        "INSERT INTO filialen (filialname, kanton, groesse, typ) VALUES (?,?,?,?)",
        (row["Filiale"], row["Kanton"], row["Filialgroesse"], row["Filialtyp"])
    )
print(f"   ✅ Tabelle 'filialen': {len(filialen_unique)} Einträge")

# ── Tabelle 2: Produkte (Dimensionstabelle) ───────────────
cur.execute("""
CREATE TABLE produkte (
    produkt_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    produktname  TEXT NOT NULL UNIQUE,
    kategorie    TEXT NOT NULL
)
""")

produkte_unique = df[["Produkt","Kategorie"]].drop_duplicates()
for _, row in produkte_unique.iterrows():
    cur.execute(
        "INSERT INTO produkte (produktname, kategorie) VALUES (?,?)",
        (row["Produkt"], row["Kategorie"])
    )
print(f"   ✅ Tabelle 'produkte': {len(produkte_unique)} Einträge")

# ── Tabelle 3: Verkäufe (Faktentabelle) ───────────────────
cur.execute("""
CREATE TABLE verkaeufe (
    transaktion_id   TEXT PRIMARY KEY,
    datum            TEXT NOT NULL,
    wochentag        TEXT NOT NULL,
    monat            TEXT NOT NULL,
    quartal          TEXT NOT NULL,
    uhrzeit          TEXT,
    filiale_id       INTEGER NOT NULL,
    produkt_id       INTEGER NOT NULL,
    menge            INTEGER NOT NULL,
    preis_chf        REAL NOT NULL,
    umsatz_chf       REAL NOT NULL,
    gewinn_chf       REAL NOT NULL,
    marge_pct        REAL NOT NULL,
    zahlungsmethode  TEXT NOT NULL,
    FOREIGN KEY (filiale_id) REFERENCES filialen(filiale_id),
    FOREIGN KEY (produkt_id) REFERENCES produkte(produkt_id)
)
""")

# IDs nachschlagen
filial_map  = pd.read_sql("SELECT filiale_id, filialname FROM filialen", conn)
filial_map  = dict(zip(filial_map["filialname"], filial_map["filiale_id"]))
produkt_map = pd.read_sql("SELECT produkt_id, produktname FROM produkte", conn)
produkt_map = dict(zip(produkt_map["produktname"], produkt_map["produkt_id"]))

for _, row in df.iterrows():
    cur.execute("""
        INSERT INTO verkaeufe VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, (
        row["Transaktion_ID"],
        row["Datum"],
        row["Wochentag"],
        row["Monat"],
        row["Quartal"],
        row["Uhrzeit"],
        filial_map[row["Filiale"]],
        produkt_map[row["Produkt"]],
        int(row["Menge"]),
        float(row["Preis_CHF"]),
        float(row["Umsatz_CHF"]),
        float(row["Gewinn_CHF"]),
        float(row["Marge_Pct"]),
        row["Zahlungsmethode"]
    ))

conn.commit()
print(f"   ✅ Tabelle 'verkaeufe': {len(df):,} Einträge")

# ── Tabelle 4: Vordefinierte Analysen (Views) ─────────────
cur.execute("""
CREATE VIEW v_umsatz_pro_filiale AS
SELECT
    f.filialname,
    f.kanton,
    f.groesse,
    COUNT(v.transaktion_id)      AS anzahl_transaktionen,
    ROUND(SUM(v.umsatz_chf), 2)  AS total_umsatz_chf,
    ROUND(SUM(v.gewinn_chf), 2)  AS total_gewinn_chf,
    ROUND(AVG(v.umsatz_chf), 2)  AS avg_bon_chf,
    ROUND(SUM(v.gewinn_chf) / SUM(v.umsatz_chf) * 100, 1) AS marge_pct
FROM verkaeufe v
JOIN filialen f ON v.filiale_id = f.filiale_id
GROUP BY f.filialname
ORDER BY total_umsatz_chf DESC
""")

cur.execute("""
CREATE VIEW v_umsatz_pro_kategorie AS
SELECT
    p.kategorie,
    COUNT(v.transaktion_id)      AS anzahl_transaktionen,
    ROUND(SUM(v.umsatz_chf), 2)  AS total_umsatz_chf,
    ROUND(SUM(v.gewinn_chf), 2)  AS total_gewinn_chf,
    ROUND(SUM(v.gewinn_chf) / SUM(v.umsatz_chf) * 100, 1) AS marge_pct
FROM verkaeufe v
JOIN produkte p ON v.produkt_id = p.produkt_id
GROUP BY p.kategorie
ORDER BY total_umsatz_chf DESC
""")

cur.execute("""
CREATE VIEW v_top_produkte AS
SELECT
    p.produktname,
    p.kategorie,
    COUNT(v.transaktion_id)      AS transaktionen,
    SUM(v.menge)                 AS total_menge,
    ROUND(SUM(v.umsatz_chf), 2)  AS total_umsatz_chf,
    ROUND(SUM(v.gewinn_chf), 2)  AS total_gewinn_chf,
    ROUND(SUM(v.gewinn_chf) / SUM(v.umsatz_chf) * 100, 1) AS marge_pct
FROM verkaeufe v
JOIN produkte p ON v.produkt_id = p.produkt_id
GROUP BY p.produktname
ORDER BY total_umsatz_chf DESC
""")

cur.execute("""
CREATE VIEW v_monatstrend AS
SELECT
    monat,
    quartal,
    COUNT(transaktion_id)        AS transaktionen,
    ROUND(SUM(umsatz_chf), 2)    AS umsatz_chf,
    ROUND(SUM(gewinn_chf), 2)    AS gewinn_chf
FROM verkaeufe
GROUP BY monat
""")

conn.commit()
print(f"   ✅ 4 SQL-Views erstellt (v_umsatz_pro_filiale, v_top_produkte, ...)")

# ── Test-Queries ──────────────────────────────────────────
print("\n📊 Test-Abfragen:")
total = cur.execute("SELECT COUNT(*), ROUND(SUM(umsatz_chf),2) FROM verkaeufe").fetchone()
print(f"   Transaktionen: {total[0]:,} | Gesamtumsatz: CHF {total[1]:,.2f}")

beste = cur.execute("SELECT filialname, total_umsatz_chf FROM v_umsatz_pro_filiale LIMIT 1").fetchone()
print(f"   Beste Filiale: {beste[0]} mit CHF {beste[1]:,.2f}")

top_prod = cur.execute("SELECT produktname, total_umsatz_chf FROM v_top_produkte LIMIT 1").fetchone()
print(f"   Top-Produkt:   {top_prod[0]} mit CHF {top_prod[1]:,.2f}")

conn.close()

print(f"""
✅ Datenbank '{DB_DATEI}' erfolgreich erstellt!

   Tabellen:
   • filialen   – 8 Filialen (Dimensionstabelle)
   • produkte   – 30 Produkte (Dimensionstabelle)
   • verkaeufe  – 10'000 Transaktionen (Faktentabelle)

   Views (vordefinierte SQL-Abfragen):
   • v_umsatz_pro_filiale
   • v_umsatz_pro_kategorie
   • v_top_produkte
   • v_monatstrend

→ Jetzt Schritt 3 ausführen: python schritt3_agent.py
""")
