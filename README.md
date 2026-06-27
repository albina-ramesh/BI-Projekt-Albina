# 🛒 Agentic AI für Business Intelligence bei FreshMart

**Autor:** Albina Ramesh
**Kurs:** Business Intelligence
**Dozent:** Prof. Dr. Manuel Renold

**Hochschule:** FHNW – University of Applied Sciences and Arts Northwestern Switzerland
**Jahr:** 2026

---

## Unternehmensbeschreibung

FreshMart ist ein fiktives Schweizer Detailhandelsunternehmen, das sich an grossen Schweizer Retail-Unternehmen wie Migros und Coop orientiert. Das Unternehmen betreibt 8 Filialen in verschiedenen Kantonen der Schweiz und verkauft Lebensmittel, Getränke, Backwaren, Milchprodukte, Haushaltswaren und weitere Alltagsprodukte.

Im Rahmen dieses Projekts wurde eine relationale SQLite-Datenbank mit 10'000 Verkaufstransaktionen aus dem Jahr 2024 erstellt. Ziel ist es, moderne Business-Intelligence-Methoden mit Agentic AI zu kombinieren. Der entwickelte BI-Agent analysiert Verkaufsdaten, erkennt KPI-Abweichungen, vergleicht Filialen und Produktkategorien und generiert automatische Handlungsempfehlungen für das Management.

---

## Einleitung

Die Digitalisierung hat in den letzten Jahren zu einer enormen Zunahme von Unternehmensdaten geführt. Besonders im Detailhandel entstehen täglich grosse Mengen an Verkaufs-, Kunden- und Produktdaten. Unternehmen wie Migros oder Coop stehen deshalb vor der Herausforderung, diese Daten effizient auszuwerten und daraus schnelle und fundierte Entscheidungen abzuleiten. Klassische Business-Intelligence-Systeme bieten zwar Dashboards und Berichte, jedoch fehlt häufig die Fähigkeit, selbstständig Zusammenhänge zu erkennen, Analysen durchzuführen und aktiv Handlungsempfehlungen zu generieren.

Im Rahmen dieses Projekts wird deshalb ein intelligenter Business-Intelligence-Agent entwickelt. Der Agent basiert auf dem Ansatz der Agentic AI und analysiert Verkaufsdaten des fiktiven Schweizer Detailhandelsunternehmens FreshMart. Dafür wurde eine realistische, aber fiktive Datenbank erstellt, die 10'000 Verkaufstransaktionen aus dem Jahr 2024 enthält. Die Daten orientieren sich an typischen Strukturen und Prozessen eines Schweizer Retail-Unternehmens.

Das Ziel des Projekts besteht darin, einen BI-Agenten zu entwickeln, der selbstständig KPI-Abweichungen erkennt, Trends analysiert, Filialen und Kategorien vergleicht und automatische Handlungsempfehlungen erstellt. Zusätzlich wird gezeigt, wie moderne AI-Agenten mit Datenquellen (Excel, SQL-Datenbank), Analysewerkzeugen und einem Web-Interface interagieren können.

Ein weiterer Fokus liegt auf der Verbindung zwischen klassischer Business Intelligence und modernen AI-Agenten. Während traditionelle BI-Systeme vor allem Daten visualisieren, können Agentic-AI-Systeme eigenständig Analysen planen, Informationen aus verschiedenen Quellen kombinieren und proaktiv Entscheidungen unterstützen. Dadurch entsteht ein intelligenteres und dynamischeres Entscheidungsunterstützungssystem.

---

## Datenfluss

Das Projekt folgt einem klassischen BI-Datenfluss, wie er im Kurs behandelt wurde:

```
Excel (.xlsx)  →  SQLite Datenbank  →  SQL-Abfragen  →  AI-Agent  →  Antworten & Empfehlungen
```

1. **Schritt 1** – Rohdaten werden als Excel-Datei mit 4 Sheets generiert
2. **Schritt 2** – Excel-Daten werden in eine normalisierte SQLite-Datenbank geladen
3. **Schritt 3** – Der AI-Agent beantwortet Fragen via SQL-Abfragen und gibt Handlungsempfehlungen

---

## Tabellen und Datenmodell

Für das Projekt wurde ein relationales Datenmodell selbst konzipiert und umgesetzt. Das Datenmodell besteht aus drei miteinander verbundenen Tabellen sowie vier vordefinierten SQL-Views für häufige Analysen.

### Dimensionstabellen

**Tabelle `filialen`**

Enthält Informationen zu den 8 FreshMart-Filialen in der Schweiz. Dazu gehören der Filialname, der Kanton, die Filialgrösse (klein, mittel, gross) und der Filialtyp (urban, suburban, touristisch). Diese Daten ermöglichen regionale Vergleiche und helfen dabei, die Leistung einzelner Filialen zu bewerten.

| Spalte | Beschreibung |
|--------|-------------|
| filiale_id | Primärschlüssel |
| filialname | Name der Filiale (z.B. ZH-City) |
| kanton | Kanton (ZH, BS, BE, LU, SG, GE, AG) |
| groesse | klein / mittel / gross |
| typ | urban / gemischt / touristisch / suburban |

**Tabelle `produkte`**

Enthält die 30 Produkte in 10 Kategorien. Dadurch können Produkttrends und Margenunterschiede zwischen Kategorien analysiert werden.

| Spalte | Beschreibung |
|--------|-------------|
| produkt_id | Primärschlüssel |
| produktname | Name des Produkts (z.B. Vollmilch 1L) |
| kategorie | Produktkategorie (z.B. Milchprodukte, Getränke) |

### Faktentabelle

**Tabelle `verkaeufe`**

Bildet den Mittelpunkt des Datenmodells mit 10'000 Verkaufstransaktionen. Über Fremdschlüssel ist sie mit den Tabellen `filialen` und `produkte` verbunden.

| Spalte | Beschreibung |
|--------|-------------|
| transaktion_id | Primärschlüssel (z.B. TXN-00001) |
| datum | Transaktionsdatum (2024-01-01 bis 2024-12-31) |
| wochentag | Wochentag der Transaktion |
| monat | Monatsname |
| quartal | Q1 bis Q4 |
| uhrzeit | Uhrzeit der Transaktion |
| filiale_id | Fremdschlüssel → filialen |
| produkt_id | Fremdschlüssel → produkte |
| menge | Verkaufte Menge |
| preis_chf | Einzelpreis in CHF |
| umsatz_chf | Gesamtumsatz der Transaktion |
| gewinn_chf | Gewinn der Transaktion |
| marge_pct | Marge in Prozent |
| zahlungsmethode | Karte / Bargeld / TWINT / Rechnung |

### SQL-Views (vordefinierte Analysen)

| View | Beschreibung |
|------|-------------|
| `v_umsatz_pro_filiale` | Umsatz, Gewinn und Marge pro Filiale |
| `v_umsatz_pro_kategorie` | Umsatz, Gewinn und Marge pro Kategorie |
| `v_top_produkte` | Produkt-Ranking nach Umsatz |
| `v_monatstrend` | Monatlicher Umsatztrend 2024 |

---

## Datenmodellierung und Datenaufbereitung

### Ausgangslage

Für das Projekt wurde ein realistisches Datenset eines fiktiven Schweizer Detailhändlers selbst erstellt und konzipiert. Ziel war es, eine Datenbasis für Business-Intelligence-Analysen und den AI-Agenten bereitzustellen. Die Daten sollten reale Geschäftsprozesse möglichst gut abbilden.

### Überlegungen bei der Modellierung

**Filialen**
Es wurden 8 Filialen in verschiedenen Kantonen der Schweiz modelliert (Zürich, Basel, Bern, Luzern, St. Gallen, Genf, Aargau). Jede Filiale hat ein unterschiedliches Gewicht bei der Datengenerierung — grosse Stadtzentren wie ZH-City erzielen mehr Transaktionen als kleinere Standorte wie AG-Aarau.

**Produkte**
Das Sortiment umfasst 30 Produkte in 10 Kategorien: Milchprodukte, Backwaren, Fleisch, Fisch, Früchte, Gemüse, Trockenwaren, Getränke, Alkohol, Süsswaren, Heissgetränke und Haushalt. Jedes Produkt hat einen realistischen Schweizer Preis und eine produktspezifische Marge.

**Verkäufe**
Die 10'000 Transaktionen wurden mit realistischen Mustern generiert:
- **Wochentag-Faktor:** Samstag ist der umsatzstärkste Tag, Sonntag der schwächste
- **Saison-Faktor:** November und Dezember (Weihnachtszeit) erzielen höhere Umsätze
- **Uhrzeit:** Verkäufe konzentrieren sich auf die Mittagszeit und den späten Nachmittag

**Zahlungsmethoden**
Es wurden schweizweit typische Zahlungsarten berücksichtigt:
- Karte (55%)
- TWINT (22%)
- Bargeld (20%)
- Rechnung (3%)

**Preise**
Alle Preise wurden an Schweizer Gegebenheiten angepasst. Die Basispreise entsprechen realistischen Schweizer Detailhandelspreisen (z.B. Vollmilch 1L = CHF 1.85, Rotwein = CHF 12.90).

### Erweiterung des Datensatzes

| Bereich | Details |
|---------|---------|
| Filialen | 8 Standorte in 7 Kantonen |
| Produkte | 30 Produkte in 10 Kategorien |
| Transaktionen | 10'000 Verkäufe (Jahr 2024) |
| SQL-Views | 4 vordefinierte Analysen |

---

## Architektur – Agentische Analytik

```
Frage der Geschäftsleitung
        │
        ▼
  AI-Agent (LLaMA 3.3 via Groq API)
        │
        ├── get_gesamtuebersicht()      → KPI-Übersicht
        ├── get_filialen_ranking()      → Filialvergleich
        ├── get_top10_produkte()        → Produkt-Ranking
        ├── get_schwachste_produkte()   → Schwache Produkte
        ├── get_kategorien_analyse()    → Kategorienanalyse
        ├── get_monatstrend()           → Zeitreihe
        ├── get_wochentag_analyse()     → Tagesanalyse
        ├── get_quartal_vergleich()     → Q1 bis Q4
        ├── get_zahlungsmethoden()      → Payment-Mix
        └── get_handlungsempfehlungen() → Automatische Empfehlungen
                  │
                  ▼
          SQLite Datenbank
          (aus Excel geladen)
                  │
                  ▼
    Antwort + Handlungsempfehlung
    (angezeigt im Streamlit Web-Interface)
```

---

## Technologie-Stack

| Komponente | Technologie |
|------------|-------------|
| Programmiersprache | Python 3.12 |
| AI-Modell | LLaMA 3.3 70B (via Groq API) |
| Datenbank | SQLite (relationale Datenbank) |
| Rohdaten | Excel (.xlsx, 4 Sheets) |
| Datenverarbeitung | pandas, openpyxl |
| Web-Interface | Streamlit |
| API-Key Verwaltung | python-dotenv (.env) |

---

## Projektstruktur

```
freshmart-bi-agent/
├── schritt1_daten_erstellen.py  → Generiert Excel mit 10'000 Datensätzen
├── schritt2_datenbank.py        → Lädt Excel in SQLite-Datenbank
├── schritt3_agent.py            → AI-Agent (Terminal-Version)
├── app.py                       → Streamlit Web-Interface
├── freshmart_verkaufsdaten.xlsx → Excel-Rohdaten (4 Sheets)
├── requirements.txt             → Python-Libraries
├── .env.example                 → Vorlage für API-Key
├── .gitignore                   → Schützt .env und Datenbank
└── README.md                    → Diese Dokumentation
```

---

## Installation und Start

### Voraussetzungen
- Python 3.10 oder höher
- Groq API-Key (kostenlos auf [console.groq.com/keys](https://console.groq.com/keys))

### Installation

```bash
pip install -r requirements.txt
```

### API-Key konfigurieren

1. `.env.example` kopieren und umbenennen zu `.env`
2. Deinen Groq-Key eintragen:
```
GROQ_API_KEY=gsk_dein_key_hier
```

### Starten

```bash
# Schritt 1: Daten generieren (einmalig)
python schritt1_daten_erstellen.py

# Schritt 2: Datenbank aufbauen (einmalig)
python schritt2_datenbank.py

# Schritt 3: Web-Interface starten
streamlit run app.py
```

---

## Beispiel-Fragen an den Agent

| Frage | Was der Agent macht |
|-------|-------------------|
| *Zeig mir die wichtigsten Kennzahlen* | KPI-Übersicht aus der Datenbank |
| *Welches Produkt verkauft sich am besten?* | Produkt-Ranking via SQL |
| *Vergleiche alle Filialen nach Umsatz* | Filial-Ranking mit Zahlen |
| *Wie war der Trend über das Jahr?* | Monatstrend-Analyse |
| *Welche Kategorie hat die höchste Marge?* | Kategorienanalyse |
| *Was soll ich tun um den Gewinn zu steigern?* | Automatische Handlungsempfehlungen |
| *Vergleiche Q1 mit Q4* | Quartalsvergleich |

---

## Nutzen für Business Intelligence

Durch die gewählte Datenstruktur und den AI-Agenten können folgende Fragestellungen automatisch beantwortet werden:

- Welche Produkte verkaufen sich am besten und welche sollten aus dem Sortiment genommen werden?
- Welche Filialen erzielen die höchsten Umsätze?
- Welche Produktkategorien haben die höchste Marge?
- Wann kaufen Kunden am meisten ein (Wochentag, Uhrzeit, Saison)?
- Welche Handlungsempfehlungen ergeben sich für das Management?

Der AI-Agent kombiniert dabei klassische BI-Methoden (SQL-Abfragen, Aggregationen, Trends) mit modernen KI-Fähigkeiten (natürlichsprachliche Verarbeitung, automatische Empfehlungen) — genau im Sinne der Agentic Analytics.
