"""
FreshMart – Streamlit Web-Interface
Agentische Verkaufsanalytik | FHNW Business Intelligence
"""

import os
import sqlite3
import pandas as pd
import streamlit as st
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────────────────────
#  SEITEN-KONFIGURATION
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="FreshMart AI-Agent",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────
#  CSS STYLING
# ─────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a5276, #2e86c1);
        padding: 20px 30px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
    }
    .main-header h1 { color: white; margin: 0; font-size: 2rem; }
    .main-header p  { color: #d6eaf8; margin: 5px 0 0 0; font-size: 0.95rem; }

    .metric-card {
        background: white;
        border: 1px solid #d5dbdb;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.07);
    }
    .metric-card .label { color: #5d6d7e; font-size: 0.8rem; font-weight: 600; }
    .metric-card .value { color: #1a5276; font-size: 1.6rem; font-weight: 700; }

    .chat-user {
        color: #1a1a1a !important;
        background: #eaf4fb;
        border-left: 4px solid #2e86c1;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
    }
    .chat-agent {
        color: #1a1a1a !important;
        background: #eafaf1;
        border-left: 4px solid #27ae60;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
    }
    .tool-badge {
        background: #fef9e7;
        border: 1px solid #f9e79f;
        border-radius: 5px;
        padding: 2px 8px;
        font-size: 0.75rem;
        color: #7d6608;
        margin: 2px;
        display: inline-block;
    }
    .sidebar-info {
        color: #1a1a1a !important;
        background: #eaf4fb;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  DATENBANK
# ─────────────────────────────────────────────
DB_DATEI = "freshmart.db"
MODEL    = "llama-3.3-70b-versatile"

def db_query(sql: str) -> str:
    if not os.path.exists(DB_DATEI):
        return "❌ Datenbank nicht gefunden. Bitte schritt2_datenbank.py ausführen."
    try:
        conn = sqlite3.connect(DB_DATEI)
        df   = pd.read_sql_query(sql, conn)
        conn.close()
        return df.to_string(index=False) if not df.empty else "Keine Daten."
    except Exception as e:
        return f"SQL-Fehler: {e}"

def db_df(sql: str) -> pd.DataFrame:
    try:
        conn = sqlite3.connect(DB_DATEI)
        df   = pd.read_sql_query(sql, conn)
        conn.close()
        return df
    except:
        return pd.DataFrame()

# ─────────────────────────────────────────────
#  TOOL-FUNKTIONEN
# ─────────────────────────────────────────────
def get_gesamtuebersicht() -> str:
    return db_query("""
        SELECT COUNT(*) AS total_transaktionen,
               ROUND(SUM(umsatz_chf),2) AS gesamtumsatz_chf,
               ROUND(SUM(gewinn_chf),2) AS gesamtgewinn_chf,
               ROUND(AVG(umsatz_chf),2) AS avg_bon_chf,
               ROUND(SUM(gewinn_chf)/SUM(umsatz_chf)*100,1) AS marge_pct,
               COUNT(DISTINCT filiale_id) AS filialen,
               COUNT(DISTINCT produkt_id) AS produkte
        FROM verkaeufe
    """)

def get_filialen_ranking() -> str:
    return db_query("SELECT * FROM v_umsatz_pro_filiale")

def get_top10_produkte() -> str:
    return db_query("SELECT * FROM v_top_produkte LIMIT 10")

def get_schwachste_produkte() -> str:
    return db_query("SELECT * FROM v_top_produkte ORDER BY total_umsatz_chf ASC LIMIT 10")

def get_kategorien_analyse() -> str:
    return db_query("SELECT * FROM v_umsatz_pro_kategorie")

def get_monatstrend() -> str:
    return db_query("""
        SELECT monat, quartal, transaktionen, umsatz_chf, gewinn_chf
        FROM v_monatstrend
        ORDER BY CASE monat
            WHEN 'January' THEN 1 WHEN 'February' THEN 2 WHEN 'March' THEN 3
            WHEN 'April' THEN 4 WHEN 'May' THEN 5 WHEN 'June' THEN 6
            WHEN 'July' THEN 7 WHEN 'August' THEN 8 WHEN 'September' THEN 9
            WHEN 'October' THEN 10 WHEN 'November' THEN 11 WHEN 'December' THEN 12
        END
    """)

def get_wochentag_analyse() -> str:
    return db_query("""
        SELECT wochentag, COUNT(*) AS transaktionen,
               ROUND(SUM(umsatz_chf),2) AS umsatz_chf,
               ROUND(AVG(umsatz_chf),2) AS avg_bon_chf
        FROM verkaeufe GROUP BY wochentag
        ORDER BY CASE wochentag
            WHEN 'Montag' THEN 1 WHEN 'Dienstag' THEN 2 WHEN 'Mittwoch' THEN 3
            WHEN 'Donnerstag' THEN 4 WHEN 'Freitag' THEN 5
            WHEN 'Samstag' THEN 6 WHEN 'Sonntag' THEN 7
        END
    """)

def get_zahlungsmethoden() -> str:
    return db_query("""
        SELECT zahlungsmethode, COUNT(*) AS anzahl,
               ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM verkaeufe),1) AS anteil_pct,
               ROUND(SUM(umsatz_chf),2) AS umsatz_chf
        FROM verkaeufe GROUP BY zahlungsmethode ORDER BY anzahl DESC
    """)

def get_quartal_vergleich() -> str:
    return db_query("""
        SELECT quartal, COUNT(*) AS transaktionen,
               ROUND(SUM(umsatz_chf),2) AS umsatz_chf,
               ROUND(SUM(gewinn_chf),2) AS gewinn_chf,
               ROUND(SUM(gewinn_chf)/SUM(umsatz_chf)*100,1) AS marge_pct
        FROM verkaeufe GROUP BY quartal ORDER BY quartal
    """)

def get_handlungsempfehlungen() -> str:
    beste   = db_query("SELECT filialname, total_umsatz_chf FROM v_umsatz_pro_filiale LIMIT 1")
    schecht = db_query("SELECT filialname, total_umsatz_chf FROM v_umsatz_pro_filiale ORDER BY total_umsatz_chf ASC LIMIT 1")
    bkat    = db_query("SELECT kategorie, marge_pct FROM v_umsatz_pro_kategorie ORDER BY marge_pct DESC LIMIT 1")
    skat    = db_query("SELECT kategorie, marge_pct FROM v_umsatz_pro_kategorie ORDER BY marge_pct ASC LIMIT 1")
    schwach = db_query("SELECT produktname, total_umsatz_chf FROM v_top_produkte ORDER BY total_umsatz_chf ASC LIMIT 1")
    return f"""
=== HANDLUNGSEMPFEHLUNGEN – FreshMart 2024 ===
Beste Filiale:        {beste}
Schwächste Filiale:   {schecht}
Beste Kategorie:      {bkat}
Schwächste Kategorie: {skat}
Schwächstes Produkt:  {schwach}

EMPFEHLUNGEN:
1. Best-Practice-Transfer der besten Filiale auf schwächere übertragen.
2. Schwächstes Produkt aus Sortiment nehmen oder Preis senken.
3. Kategorie mit höchster Marge im Regal priorisieren.
4. Sonntag mit Spezialaktionen stärken.
5. Lieferantenverhandlung bei schwächster Kategorie.
"""

TOOLS = [
    {"type":"function","function":{"name":"get_gesamtuebersicht","description":"Gesamtkennzahlen FreshMart (Umsatz, Gewinn, Marge).","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_filialen_ranking","description":"Ranking aller Filialen nach Umsatz.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_top10_produkte","description":"Top 10 Produkte nach Umsatz.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_schwachste_produkte","description":"Die 10 schwächsten Produkte.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_kategorien_analyse","description":"Umsatz und Marge nach Kategorie.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_monatstrend","description":"Monatlicher Umsatztrend 2024.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_wochentag_analyse","description":"Umsatz nach Wochentag.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_zahlungsmethoden","description":"Verteilung der Zahlungsmethoden.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_quartal_vergleich","description":"Quartalsvergleich Q1-Q4.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_handlungsempfehlungen","description":"Konkrete Handlungsempfehlungen basierend auf allen Daten.","parameters":{"type":"object","properties":{},"required":[]}}},
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
Datenbasis: SQLite-Datenbank mit 10'000 Verkaufstransaktionen aus 2024 (aus Excel geladen).
Antworte immer auf Deutsch, präzise und mit konkreten Zahlen.
Nutze immer zuerst die Tools um aktuelle Daten abzurufen."""

# ─────────────────────────────────────────────
#  AGENT FUNKTION
# ─────────────────────────────────────────────
def run_agent(frage: str, client: Groq, history: list):
    history.append({"role": "user", "content": frage})
    tools_used = []

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
            result = fn() if fn else "Unbekanntes Tool"
            tools_used.append(tc.function.name)
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
    return antwort, tools_used

# ─────────────────────────────────────────────
#  STREAMLIT UI
# ─────────────────────────────────────────────

# Session State initialisieren
if "history" not in st.session_state:
    st.session_state.history = []
if "messages" not in st.session_state:
    st.session_state.messages = []
if "client" not in st.session_state:
    api_key = os.getenv("GROQ_API_KEY", "")
    st.session_state.client = Groq(api_key=api_key) if api_key else None

# ── Header ────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🛒 FreshMart AI-Agent</h1>
    <p>Agentische Verkaufsanalytik | BI-Projekt FHNW 2026 von Albina Ramesh</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/color/96/shopping-cart.png", width=60)
    st.title("FreshMart")
    st.caption("Business Intelligence")

    st.markdown("---")
    st.markdown("### 📊 Datenbank-Info")
    if os.path.exists(DB_DATEI):
        conn = sqlite3.connect(DB_DATEI)
        total = pd.read_sql("SELECT COUNT(*) as n FROM verkaeufe", conn).iloc[0,0]
        umsatz = pd.read_sql("SELECT ROUND(SUM(umsatz_chf),0) as u FROM verkaeufe", conn).iloc[0,0]
        conn.close()
        st.markdown(f"""
        <div class="sidebar-info">
        ✅ Datenbank verbunden<br>
        📦 {total:,} Transaktionen<br>
        💰 CHF {umsatz:,.0f} Umsatz<br>
        🏪 8 Filialen | 30 Produkte
        </div>
        """, unsafe_allow_html=True)
    else:
        st.error("❌ Datenbank nicht gefunden!\nBitte schritt2_datenbank.py ausführen.")

    st.markdown("---")
    st.markdown("### 💡 Beispiel-Fragen")
    beispiele = [
        "Zeig mir die wichtigsten Kennzahlen",
        "Welches Produkt verkauft sich am besten?",
        "Vergleiche alle Filialen nach Umsatz",
        "Wie war der Trend über das Jahr?",
        "Welche Kategorie hat die höchste Marge?",
        "Was soll ich tun um den Gewinn zu steigern?",
        "Wann kaufen Kunden am meisten ein?",
        "Vergleiche Q1 mit Q4",
    ]
    for b in beispiele:
        if st.button(b, use_container_width=True, key=f"btn_{b}"):
            st.session_state["pending_question"] = b

    st.markdown("---")
    if st.button("🗑️ Chat leeren", use_container_width=True):
        st.session_state.history = []
        st.session_state.messages = []
        st.rerun()

# ── Kennzahlen oben ───────────────────────────
if os.path.exists(DB_DATEI):
    conn = sqlite3.connect(DB_DATEI)
    kz = pd.read_sql("""
        SELECT ROUND(SUM(umsatz_chf),2) as umsatz,
               ROUND(SUM(gewinn_chf),2) as gewinn,
               ROUND(SUM(gewinn_chf)/SUM(umsatz_chf)*100,1) as marge,
               ROUND(AVG(umsatz_chf),2) as avg_bon
        FROM verkaeufe
    """, conn)
    conn.close()

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("💰 Gesamtumsatz", f"CHF {kz['umsatz'].iloc[0]:,.0f}")
    with c2:
        st.metric("📈 Gesamtgewinn", f"CHF {kz['gewinn'].iloc[0]:,.0f}")
    with c3:
        st.metric("📊 Marge", f"{kz['marge'].iloc[0]}%")
    with c4:
        st.metric("🧾 Ø Bon", f"CHF {kz['avg_bon'].iloc[0]:.2f}")

    st.markdown("---")

# ── Chat-Bereich ──────────────────────────────
st.markdown("### 🤖 Chat mit dem AI-Agent")

# Vorherige Nachrichten anzeigen
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-user">👤 <b>Du:</b> {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        tools_html = ""
        if msg.get("tools"):
            tools_html = " ".join([f'<span class="tool-badge">🔧 {t}</span>' for t in msg["tools"]])
        st.markdown(f'<div class="chat-agent">🤖 <b>FreshMart Agent:</b><br>{tools_html}<br>{msg["content"]}</div>', unsafe_allow_html=True)

# Eingabe
frage = st.chat_input("Stelle eine Frage zu den FreshMart Verkaufsdaten...")

# Button-Frage verarbeiten
if "pending_question" in st.session_state:
    frage = st.session_state.pop("pending_question")

if frage:
    if not st.session_state.client:
        st.error("❌ Kein Groq API-Key gefunden! Bitte .env Datei mit GROQ_API_KEY erstellen.")
    elif not os.path.exists(DB_DATEI):
        st.error("❌ Datenbank nicht gefunden! Bitte schritt2_datenbank.py ausführen.")
    else:
        st.session_state.messages.append({"role": "user", "content": frage})
        st.markdown(f'<div class="chat-user">👤 <b>Du:</b> {frage}</div>', unsafe_allow_html=True)

        with st.spinner("🤖 Agent analysiert Daten..."):
            antwort, tools_used = run_agent(frage, st.session_state.client, st.session_state.history)

        st.session_state.messages.append({
            "role": "assistant",
            "content": antwort,
            "tools": tools_used
        })

        tools_html = " ".join([f'<span class="tool-badge">🔧 {t}</span>' for t in tools_used])
        st.markdown(f'<div class="chat-agent">🤖 <b>FreshMart Agent:</b><br>{tools_html}<br>{antwort}</div>', unsafe_allow_html=True)
        st.rerun()
