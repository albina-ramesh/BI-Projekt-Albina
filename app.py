"""
FreshMart – Streamlit Web-Interface mit Diagrammen
Agentische Verkaufsanalytik | FHNW Business Intelligence
"""

import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="FreshMart AI-Agent",
    page_icon="🛒",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    .chat-user {
        background: #eaf4fb;
        border-left: 4px solid #2e86c1;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
        color: #1a1a1a !important;
    }
    .chat-agent {
        background: #eafaf1;
        border-left: 4px solid #27ae60;
        padding: 12px 16px;
        border-radius: 8px;
        margin: 8px 0;
        color: #1a1a1a !important;
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
        background: #eaf4fb;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
        font-size: 0.85rem;
        color: #1a1a1a !important;
    }
</style>
""", unsafe_allow_html=True)

DB_DATEI = "freshmart.db"
MODEL    = "llama-3.3-70b-versatile"

def db_query(sql: str) -> str:
    if not os.path.exists(DB_DATEI):
        return "❌ Datenbank nicht gefunden."
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

# ── Tool-Funktionen ───────────────────────────
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
    {"type":"function","function":{"name":"get_gesamtuebersicht","description":"Gesamtkennzahlen FreshMart.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_filialen_ranking","description":"Ranking aller Filialen nach Umsatz.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_top10_produkte","description":"Top 10 Produkte nach Umsatz.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_schwachste_produkte","description":"Die 10 schwächsten Produkte.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_kategorien_analyse","description":"Umsatz und Marge nach Kategorie.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_monatstrend","description":"Monatlicher Umsatztrend 2024.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_wochentag_analyse","description":"Umsatz nach Wochentag.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_zahlungsmethoden","description":"Verteilung der Zahlungsmethoden.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_quartal_vergleich","description":"Quartalsvergleich Q1-Q4.","parameters":{"type":"object","properties":{},"required":[]}}},
    {"type":"function","function":{"name":"get_handlungsempfehlungen","description":"Handlungsempfehlungen für das Management.","parameters":{"type":"object","properties":{},"required":[]}}},
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

SYSTEM_PROMPT = """Du bist ein Business Intelligence AI-Agent für FreshMart Schweiz.
Datenbasis: SQLite-Datenbank mit 10'000 Verkaufstransaktionen aus 2024.
Antworte immer auf Deutsch, präzise und mit konkreten Zahlen.
Nutze immer zuerst die Tools um aktuelle Daten abzurufen."""

def run_agent(frage: str, client: Groq, history: list):
    history.append({"role": "user", "content": frage})
    tools_used = []
    response = client.chat.completions.create(
        model=MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + history,
        tools=TOOLS, tool_choice="auto", max_tokens=1500
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

# ── Session State ─────────────────────────────
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
    <p>Agentische Verkaufsanalytik | Business Intelligence FHNW | ffnlw04 | Prof. Dr. Manuel Renold</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ───────────────────────────────────
with st.sidebar:
    st.title("🛒 FreshMart")
    st.caption("BI-Projekt FHNW 2024")
    st.markdown("---")
    st.markdown("### 📊 Datenbank-Info")
    if os.path.exists(DB_DATEI):
        conn = sqlite3.connect(DB_DATEI)
        total  = pd.read_sql("SELECT COUNT(*) as n FROM verkaeufe", conn).iloc[0,0]
        umsatz = pd.read_sql("SELECT ROUND(SUM(umsatz_chf),0) as u FROM verkaeufe", conn).iloc[0,0]
        conn.close()
        st.markdown(f"""<div class="sidebar-info">
        ✅ Datenbank verbunden<br>
        📦 {total:,} Transaktionen<br>
        💰 CHF {umsatz:,.0f} Umsatz<br>
        🏪 8 Filialen | 30 Produkte
        </div>""", unsafe_allow_html=True)
    else:
        st.error("❌ Datenbank nicht gefunden!")

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

# ── Kennzahlen ────────────────────────────────
if os.path.exists(DB_DATEI):
    conn = sqlite3.connect(DB_DATEI)
    kz = pd.read_sql("""
        SELECT ROUND(SUM(umsatz_chf),2) as umsatz,
               ROUND(SUM(gewinn_chf),2) as gewinn,
               ROUND(SUM(gewinn_chf)/SUM(umsatz_chf)*100,1) as marge,
               ROUND(AVG(umsatz_chf),2) as avg_bon,
               COUNT(*) as tx
        FROM verkaeufe
    """, conn)
    conn.close()

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💰 Gesamtumsatz", f"CHF {kz['umsatz'].iloc[0]:,.0f}")
    c2.metric("📈 Gesamtgewinn", f"CHF {kz['gewinn'].iloc[0]:,.0f}")
    c3.metric("📊 Marge", f"{kz['marge'].iloc[0]}%")
    c4.metric("🧾 Ø Bon", f"CHF {kz['avg_bon'].iloc[0]:.2f}")
    c5.metric("🔢 Transaktionen", f"{kz['tx'].iloc[0]:,}")

    st.markdown("---")

    # ── Diagramme ─────────────────────────────
    st.markdown("### 📊 Dashboards")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🏪 Filialen", "📦 Produkte", "📈 Monatstrend", "📅 Wochentage", "💳 Zahlungen"
    ])

    with tab1:
        conn = sqlite3.connect(DB_DATEI)
        df_fil = pd.read_sql("SELECT * FROM v_umsatz_pro_filiale", conn)
        conn.close()
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(df_fil, x="filialname", y="total_umsatz_chf",
                        title="Umsatz pro Filiale (CHF)",
                        color="total_umsatz_chf",
                        color_continuous_scale="Blues",
                        labels={"filialname":"Filiale","total_umsatz_chf":"Umsatz CHF"})
            fig.update_layout(showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig2 = px.bar(df_fil, x="filialname", y="marge_pct",
                         title="Marge pro Filiale (%)",
                         color="marge_pct",
                         color_continuous_scale="Greens",
                         labels={"filialname":"Filiale","marge_pct":"Marge %"})
            fig2.update_layout(showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(df_fil, use_container_width=True, hide_index=True)

    with tab2:
        conn = sqlite3.connect(DB_DATEI)
        df_prod = pd.read_sql("SELECT * FROM v_top_produkte LIMIT 15", conn)
        conn.close()
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(df_prod.head(10), x="total_umsatz_chf", y="produktname",
                        orientation="h",
                        title="Top 10 Produkte nach Umsatz",
                        color="total_umsatz_chf",
                        color_continuous_scale="Blues",
                        labels={"produktname":"Produkt","total_umsatz_chf":"Umsatz CHF"})
            fig.update_layout(showlegend=False, coloraxis_showscale=False, yaxis={"categoryorder":"total ascending"})
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            conn = sqlite3.connect(DB_DATEI)
            df_kat = pd.read_sql("SELECT * FROM v_umsatz_pro_kategorie", conn)
            conn.close()
            fig2 = px.pie(df_kat, values="total_umsatz_chf", names="kategorie",
                         title="Umsatzanteil nach Kategorie",
                         color_discrete_sequence=px.colors.qualitative.Set3)
            st.plotly_chart(fig2, use_container_width=True)
        st.dataframe(df_prod, use_container_width=True, hide_index=True)

    with tab3:
        conn = sqlite3.connect(DB_DATEI)
        df_mon = pd.read_sql("""
            SELECT monat, quartal, umsatz_chf, gewinn_chf, transaktionen FROM v_monatstrend
            ORDER BY CASE monat
                WHEN 'January' THEN 1 WHEN 'February' THEN 2 WHEN 'March' THEN 3
                WHEN 'April' THEN 4 WHEN 'May' THEN 5 WHEN 'June' THEN 6
                WHEN 'July' THEN 7 WHEN 'August' THEN 8 WHEN 'September' THEN 9
                WHEN 'October' THEN 10 WHEN 'November' THEN 11 WHEN 'December' THEN 12
            END
        """, conn)
        conn.close()
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_mon["monat"], y=df_mon["umsatz_chf"],
                                name="Umsatz CHF", mode="lines+markers",
                                line=dict(color="#2e86c1", width=3),
                                marker=dict(size=8)))
        fig.add_trace(go.Scatter(x=df_mon["monat"], y=df_mon["gewinn_chf"],
                                name="Gewinn CHF", mode="lines+markers",
                                line=dict(color="#27ae60", width=3),
                                marker=dict(size=8)))
        fig.update_layout(title="Monatstrend 2024 – Umsatz & Gewinn",
                         xaxis_title="Monat", yaxis_title="CHF")
        st.plotly_chart(fig, use_container_width=True)

        fig2 = px.bar(df_mon, x="monat", y="transaktionen",
                     color="quartal", title="Transaktionen pro Monat",
                     labels={"monat":"Monat","transaktionen":"Anzahl Transaktionen"})
        st.plotly_chart(fig2, use_container_width=True)

    with tab4:
        conn = sqlite3.connect(DB_DATEI)
        df_wd = pd.read_sql("""
            SELECT wochentag, COUNT(*) AS transaktionen,
                   ROUND(SUM(umsatz_chf),2) AS umsatz_chf,
                   ROUND(AVG(umsatz_chf),2) AS avg_bon_chf
            FROM verkaeufe GROUP BY wochentag
            ORDER BY CASE wochentag
                WHEN 'Montag' THEN 1 WHEN 'Dienstag' THEN 2 WHEN 'Mittwoch' THEN 3
                WHEN 'Donnerstag' THEN 4 WHEN 'Freitag' THEN 5
                WHEN 'Samstag' THEN 6 WHEN 'Sonntag' THEN 7
            END
        """, conn)
        conn.close()
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(df_wd, x="wochentag", y="umsatz_chf",
                        title="Umsatz nach Wochentag",
                        color="umsatz_chf", color_continuous_scale="Blues",
                        labels={"wochentag":"Wochentag","umsatz_chf":"Umsatz CHF"})
            fig.update_layout(showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig2 = px.bar(df_wd, x="wochentag", y="avg_bon_chf",
                         title="Durchschnittlicher Bon nach Wochentag",
                         color="avg_bon_chf", color_continuous_scale="Greens",
                         labels={"wochentag":"Wochentag","avg_bon_chf":"Ø Bon CHF"})
            fig2.update_layout(showlegend=False, coloraxis_showscale=False)
            st.plotly_chart(fig2, use_container_width=True)

    with tab5:
        conn = sqlite3.connect(DB_DATEI)
        df_zahl = pd.read_sql("""
            SELECT zahlungsmethode, COUNT(*) AS anzahl,
                   ROUND(COUNT(*)*100.0/(SELECT COUNT(*) FROM verkaeufe),1) AS anteil_pct,
                   ROUND(SUM(umsatz_chf),2) AS umsatz_chf
            FROM verkaeufe GROUP BY zahlungsmethode ORDER BY anzahl DESC
        """, conn)
        conn.close()
        col1, col2 = st.columns(2)
        with col1:
            fig = px.pie(df_zahl, values="anzahl", names="zahlungsmethode",
                        title="Zahlungsmethoden nach Anzahl",
                        color_discrete_sequence=["#2e86c1","#27ae60","#e67e22","#8e44ad"])
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            fig2 = px.bar(df_zahl, x="zahlungsmethode", y="umsatz_chf",
                         title="Umsatz nach Zahlungsmethode",
                         color="zahlungsmethode",
                         color_discrete_sequence=["#2e86c1","#27ae60","#e67e22","#8e44ad"],
                         labels={"zahlungsmethode":"Methode","umsatz_chf":"Umsatz CHF"})
            fig2.update_layout(showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

# ── Chat ──────────────────────────────────────
st.markdown("### 🤖 Chat mit dem AI-Agent")

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="chat-user">👤 <b>Du:</b> {msg["content"]}</div>', unsafe_allow_html=True)
    else:
        tools_html = " ".join([f'<span class="tool-badge">🔧 {t}</span>' for t in msg.get("tools",[])])
        st.markdown(f'<div class="chat-agent">🤖 <b>FreshMart Agent:</b><br>{tools_html}<br>{msg["content"]}</div>', unsafe_allow_html=True)

frage = st.chat_input("Stelle eine Frage zu den FreshMart Verkaufsdaten...")

if "pending_question" in st.session_state:
    frage = st.session_state.pop("pending_question")

if frage:
    if not st.session_state.client:
        st.error("❌ Kein Groq API-Key! Bitte .env Datei mit GROQ_API_KEY erstellen.")
    elif not os.path.exists(DB_DATEI):
        st.error("❌ Datenbank nicht gefunden! Bitte schritt2_datenbank.py ausführen.")
    else:
        st.session_state.messages.append({"role": "user", "content": frage})
        st.markdown(f'<div class="chat-user">👤 <b>Du:</b> {frage}</div>', unsafe_allow_html=True)
        with st.spinner("🤖 Agent analysiert Daten..."):
            antwort, tools_used = run_agent(frage, st.session_state.client, st.session_state.history)
        st.session_state.messages.append({"role": "assistant", "content": antwort, "tools": tools_used})
        tools_html = " ".join([f'<span class="tool-badge">🔧 {t}</span>' for t in tools_used])
        st.markdown(f'<div class="chat-agent">🤖 <b>FreshMart Agent:</b><br>{tools_html}<br>{antwort}</div>', unsafe_allow_html=True)
        st.rerun()
