import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date

# Configuración de la pantalla
st.set_page_config(page_title="Trading Journal Pro", layout="wide", initial_sidebar_state="expanded")

# ID de la NUEVA hoja de Google Sheets de tu amiga
SPREADSHEET_ID = "1Dst-Xpe9S8dquIzoLDaMUxGUHZx9yhHOufTRgnkp_PI"
CSV_URL = f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/export?format=csv"

# Configuración de la cuenta por defecto
CAPITAL_INICIAL = 50000.0
COLOR_GANANCIA = "#2ec4b6"
COLOR_PERDIDA = "#e63946"

# Lista de confirmaciones predeterminadas
REGLAS_DEFECTO = [
    "Dirección",
    "CRT 1H, 3H, 4H, 1D",
    "iFVG",
    "CISD",
    "TOS",
    "Horarios 9:00 AM a 10:30 AM",
    "⚠️​Respete Mi Plan ⚠️​",
    "SI ☺️​",
    "NO 🥺​"
]

# Inicializar sesión local si no existe
if "checklist_custom" not in st.session_state:
    st.session_state["checklist_custom"] = REGLAS_DEFECTO.copy()

# Función para cargar datos desde Google Sheets
@st.cache_data(ttl=5)
def cargar_datos_sheets():
    try:
        df = pd.read_csv(CSV_URL)
        if not df.empty and "fecha" in df.columns:
            df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce").fillna(0.0)
            df["num_trades"] = pd.to_numeric(df["num_trades"], errors="coerce").fillna(1).astype(int)
            df["fecha"] = df["fecha"].astype(str)
            return df
    except Exception:
        pass
    return pd.DataFrame(columns=["id", "fecha", "pnl", "num_trades", "confirmaciones", "foto_antes", "foto_despues", "notas"])

df_all = cargar_datos_sheets()

# MÉTRICAS GENERALES
total_pnl = df_all['pnl'].sum() if not df_all.empty else 0.0
balance_final = CAPITAL_INICIAL + total_pnl
total_trades = df_all['num_trades'].sum() if not df_all.empty else 0

wins = df_all[df_all['pnl'] > 0]
losses = df_all[df_all['pnl'] < 0]

num_wins = len(wins)
num_losses = len(losses)
total_registros = len(df_all)

win_rate = (num_wins / total_registros * 100) if total_registros > 0 else 0.0
ave_win = wins['pnl'].mean() if not wins.empty else 0.0
ave_loss = abs(losses['pnl'].mean()) if not losses.empty else 0.0
profit_factor = (wins['pnl'].sum() / abs(losses['pnl'].sum())) if not losses.empty and losses['pnl'].sum() != 0 else (wins['pnl'].sum() if not wins.empty else 0.0)

# --- HEADER DE MÉTRICAS ---
st.title("🚀 Trading Journal Pro")

m1, m2, m3, m4 = st.columns(4)
m1.metric("Capital Inicial", f"${CAPITAL_INICIAL:,.2f}")
m2.metric("Net Profit / Loss", f"${total_pnl:,.2f}", delta=f"${total_pnl:,.2f}")
m3.metric("Balance Final", f"${balance_final:,.2f}")
m4.metric("Win Rate", f"{win_rate:.1f}%")

st.divider()

# --- PESTAÑAS PRINCIPALES ---
tab_dash, tab_cal, tab_reg, tab_bal, tab_config = st.tabs([
    "📊 Dashboard & Analytics", 
    "📅 Calendario Mensual", 
    "📝 Registrar & Inspeccionar Trade", 
    "⚖️ Balanzas 2.0 (Calculadora de Cobertura)",
    "⚙️ Configuración"
])

# --- TAB 1: DASHBOARD ---
with tab_dash:
    st.subheader("📈 Analítica Global de Rendimiento")
    col_stat1, col_stat2 = st.columns(2)
    
    with col_stat1:
        st.markdown("### 🎯 Métricas de Operaciones")
        s1, s2 = st.columns(2)
        s1.write(f"**Total Trades Tomados:** {total_trades}")
        s1.write(f"**Días Ganadores:** {num_wins}")
        s1.write(f"**Días Perdedores:** {num_losses}")
        
        s2.write(f"**Ganancia Promedio:** ${ave_win:,.2f}")
        s2.write(f"**Pérdida Promedio:** ${ave_loss:,.2f}")
        s2.write(f"**Profit Factor:** {profit_factor:.2f}")

    with col_stat2:
        st.markdown("### 📊 Curva de Rendimiento Acumulado")
        if not df_all.empty:
            df_plot = df_all.copy()
            df_plot['pnl_acumulado'] = df_plot['pnl'].cumsum() + CAPITAL_INICIAL
            st.line_chart(df_plot.set_index('fecha')['pnl_acumulado'])
        else:
            st.info("Registra trades para visualizar la curva de rendimiento.")

# --- TAB 2: CALENDARIO ---
with tab_cal:
    st.subheader("📅 Calendario Mensual de Resultados")
    col_m, col_y = st.columns(2)
    mes_sel = col_m.selectbox("Mes", list(range(1, 13)),