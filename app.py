import streamlit as st
import pandas as pd
import calendar
from datetime import datetime, date

# Configuración de la pantalla
st.set_page_config(page_title="Trading Journal Pro", layout="wide", initial_sidebar_state="expanded")

# ID de la hoja de Google Sheets de tu amiga
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
    mes_sel = col_m.selectbox("Mes", list(range(1, 13)), index=datetime.now().month - 1)
    anio_sel = col_y.number_input("Año", value=datetime.now().year)

    if not df_all.empty:
        df_filtered = df_all[df_all['fecha'].str.startswith(f"{anio_sel}-{mes_sel:02d}")]
        dict_trades = df_filtered.groupby('fecha').agg({'pnl': 'sum', 'num_trades': 'sum'}).to_dict(orient='index')
    else:
        dict_trades = {}

    cal = calendar.monthcalendar(int(anio_sel), int(mes_sel))
    dias_semana = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]
    
    cols_hdr = st.columns(7)
    for idx, d in enumerate(dias_semana):
        cols_hdr[idx].markdown(f"**{d}**")

    for semana in cal:
        cols = st.columns(7)
        for i, dia in enumerate(semana):
            if dia == 0:
                cols[i].write("")
            else:
                f_key = f"{anio_sel}-{mes_sel:02d}-{dia:02d}"
                if f_key in dict_trades:
                    pnl_val = dict_trades[f_key]['pnl']
                    cnt_trades = dict_trades[f_key]['num_trades']
                    
                    selected_color = COLOR_GANANCIA if pnl_val >= 0 else COLOR_PERDIDA
                    
                    cols[i].markdown(
                        f"""
                        <div style="background-color: {selected_color}22; padding: 8px; border-radius: 6px; text-align: center; color: {selected_color}; border: 1px solid {selected_color};">
                            <b>{dia}</b><br/>
                            <small>${pnl_val:,.1f}</small><br/>
                            <small>{cnt_trades} trade(s)</small>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
                else:
                    cols[i].markdown(
                        f"""
                        <div style="padding: 8px; border: 1px solid #333; border-radius: 6px; text-align: center; color: #888;">
                            <b>{dia}</b><br/><small>-</small>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )

# --- TAB 3: REGISTRO E INSPECCIÓN ---
with tab_reg:
    c_reg, c_insp = st.columns([1.2, 1.8])
    
    with c_reg:
        st.subheader("📝 Nuevo Registro")
        fecha_sel = st.date_input("Fecha", date.today())
        fecha_str = fecha_sel.strftime("%Y-%m-%d")

        st.markdown("**💰 PnL del Día ($)**")
        col_tipo, col_monto = st.columns([1, 2])
        
        tipo_pnl = col_tipo.radio("Tipo de Resultado", ["🟢 Ganancia (+)", "🔴 Pérdida (-)"], horizontal=False)
        
        opciones_montos = [100, 150, 200, 250, 400, 500, 600, 1000, 1500, 2000, 2500, 3000, 3500, 4000, 5000, "Otro monto..."]
        monto_sel = col_monto.selectbox("Seleccionar Monto ($):", opciones_montos, index=2)
        
        if monto_sel == "Otro monto...":
            monto_final = st.number_input("Escribe el monto exacto ($)", value=100.0, step=10.0)
        else:
            monto_final = float(monto_sel)

        pnl_input = monto_final if tipo_pnl == "🟢 Ganancia (+)" else -monto_final
        st.caption(f"Valor a registrar: **${pnl_input:,.2f}**")

        trades_count = st.number_input("Número de trades", min_value=1, value=1)

        st.markdown("**📋 Checklist de Confirmaciones**")
        respuestas_checklist = []
        for idx, regla in enumerate(st.session_state["checklist_custom"]):
            if st.checkbox(regla, key=f"chk_tab_{idx}"):
                respuestas_checklist.append(regla)

        st.markdown("**🖼️ Captura ANTES del Trade**")
        url_antes = st.text_input("Pegar Link TradingView (ANTES):", placeholder="https://www.tradingview.com/x/...")

        st.markdown("**🖼️ Captura DESPUÉS del Trade**")
        url_despues = st.text_input("Pegar Link TradingView (DESPUÉS):", placeholder="https://www.tradingview.com/x/...")

        notas_input = st.text_area("Notas / Lecciones del día")

        st.info("💡 Abre el enlace de tu hoja para agregar o editar tus registros:")
        st.markdown(f"[👉 Abrir Google Sheets de tu Bitácora](https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/edit)")

    with c_insp:
        st.subheader("🔍 Detalle e Inspección de Trades")
        fecha_consulta = st.date_input("Seleccionar fecha", date.today(), key="consulta_tab")
        f_consulta_str = fecha_consulta.strftime("%Y-%m-%d")

        if not df_all.empty:
            registros = df_all[df_all['fecha'] == f_consulta_str]
        else:
            registros = pd.DataFrame()

        if not registros.empty:
            for idx, r in registros.iterrows():
                trade_id = r.get('id', idx + 1)
                pnl_val = r.get('pnl', 0.0)
                
                st.markdown(f"### Trade #{trade_id} - PnL: **${pnl_val:,.2f}**")
                st.write(f"**Número de trades:** {r.get('num_trades', 1)}")
                
                conf_str = str(r.get('confirmaciones', ''))
                confirmaciones_hechas = conf_str.split(" | ") if conf_str and conf_str != 'nan' else []
                st.write(f"**Confirmaciones cumplidas ({len(confirmaciones_hechas)}):**")
                for conf in confirmaciones_hechas:
                    if conf:
                        st.caption(f"✓ {conf}")

                notas_val = str(r.get('notas', ''))
                if notas_val and notas_val != 'nan':
                    st.info(f"**Notas:** {notas_val}")
                
                col_img1, col_img2 = st.columns(2)
                
                with col_img1:
                    st.markdown("**Captura ANTES:**")
                    link_antes = str(r.get('foto_antes', ''))
                    if link_antes and link_antes.startswith("http"):
                        st.image(link_antes, caption="Antes", use_container_width=True)
                    else:
                        st.caption("Sin captura cargada.")

                with col_img2:
                    st.markdown("**Captura DESPUÉS:**")
                    link_despues = str(r.get('foto_despues', ''))
                    if link_despues and link_despues.startswith("http"):
                        st.image(link_despues, caption="Después", use_container_width=True)
                    else:
                        st.caption("Sin captura cargada.")

                st.divider()
        else:
            st.warning("No hay registros en esta fecha.")

# --- TAB 4: BALANZAS 2.0 ---
with tab_bal:
    st.subheader("⚖️ Hoja Balanzas 2.0 (Calculadora de Cobertura Lucid / Exness)")
    st.caption("Los valores de las tablas se recalculan automáticamente en cadena cuando modificas los parámetros de entrada.")

    st.markdown("### 🎛️ Parámetros de Entrada Editables")
    p1, p2, p3, p4 = st.columns(4)
    costo_lucid = p1.number_input("Costo Cuenta Lucid ($)", value=106.0, step=5.0)
    recarga_exness = p2.number_input("Recarga Cuenta Exness ($)", value=325.0, step=10.0)
    tam_challenge = p3.number_input("Tamaño de Challenge ($)", value=50000.0, step=5000.0)
    drawdown_pct = p4.number_input("Drawdown % (ej: 0.04 para 4%)", value=0.04, step=0.01, format="%.2f")

    p5, p6, p7 = st.columns(3)
    req1 = p5.number_input("Requisito 1 Fase ($)", value=1500.0, step=100.0)
    req2 = p6.number_input("Requisito 2 Fase ($)", value=1500.0, step=100.0)
    rr_ratio = p7.number_input("Ratio RR por Tiro", value=0.75, step=0.05, format="%.2f")

    drawdown_val = tam_challenge * drawdown_pct
    total_target = req1 + req2
    
    riesgo_fase1 = costo_lucid * rr_ratio
    factor_fase1 = (costo_lucid / riesgo_fase1) if riesgo_fase1 > 0 else 0
    riesgo_max_dd1 = drawdown_val * rr_ratio
    pct_riesgo_tiro1 = (req1 / tam_challenge) if tam_challenge > 0 else 0

    gasto_fase1 = riesgo_fase1
    total_gasto_fase2 = gasto_fase1 + costo_lucid
    riesgo_fase2 = total_gasto_fase2 * rr_ratio
    riesgo_max_dd2 = drawdown_val * rr_ratio

    total_gasto_exness_acum = total_gasto_fase2 + riesgo_fase2
    meta_1a2 = drawdown_val * 2
    colchon_974 = total_gasto_exness_acum * 3

    st.divider()

    st.markdown("### 🟢 ENCABEZADO FUTUROS")
    df_top = pd.DataFrame([{
        "COSTO CUENTA LUCID": f"${costo_lucid:,.2f}",
        "RECARGA CUENTA EXNESS": f"${recarga_exness:,.2f}",
        "Tamaño de Challenge": f"${tam_challenge:,.2f}",
        "Precio de Challenge": f"${costo_lucid:,.2f}",
        "Drawdown %": f"{drawdown_pct*100:.1f}%",
        "Drawdown ($)": f"${drawdown_val:,.2f}",
        "Requisito 1 Fase": f"${req1:,.2f}",
        "Requisito 2 Fase": f"${req2:,.2f}",
        "Total Target": f"${total_target:,.2f}"
    }])
    st.dataframe(df_top, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### 🔹 PRIMERA FASE 1")
    df_fase1_show = pd.DataFrame([
        {"Base ($)": f"${costo_lucid:,.2f}", "RR": f"{rr_ratio:.2f}", "Riesgo por Tiro ($)": f"${riesgo_fase1:,.2f}", "Factor / Pct": f"{factor_fase1:.3f}", "Descripción": "Porcentaje de riesgo por tiro"},
        {"Base ($)": f"${drawdown_val:,.2f}", "RR": f"{rr_ratio:.2f}", "Riesgo por Tiro ($)": f"${riesgo_max_dd1:,.2f}", "Factor / Pct": f"{pct_riesgo_tiro1*100:.2f}%", "Descripción": "Porcentaje de riesgo por tiro"}
    ])
    st.dataframe(df_fase1_show, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### 🔹 SEGUNDA FASE 2")
    st.caption("📌 *Se suma la pérdida del primer trade más la cuenta de fondeo*")
    
    df_fase2_show = pd.DataFrame([
        {"Concepto / Base": "Cálculo Gasto Exness", "Gasto Inicial ($)": f"${gasto_fase1:,.2f}", "Costo Fondeo ($)": f"${costo_lucid:,.2f}", "Total Gasto Exness ($)": f"${total_gasto_fase2:,.2f}", "RR": "-", "Riesgo Calculado ($)": "-"},
        {"Concepto / Base": "Riesgo sobre Gasto", "Gasto Inicial ($)": "-", "Costo Fondeo ($)": "-", "Total Gasto Exness ($)": f"${total_gasto_fase2:,.2f}", "RR": f"{rr_ratio:.2f}", "Riesgo Calculado ($)": f"${riesgo_fase2:,.2f}"},
        {"Concepto / Base": "Riesgo sobre Drawdown", "Gasto Inicial ($)": "-", "Costo Fondeo ($)": "-", "Total Gasto Exness ($)": f"${drawdown_val:,.2f}", "RR": f"{rr_ratio:.2f}", "Riesgo Calculado ($)": f"${riesgo_max_dd2:,.2f}"}
    ])
    st.dataframe(df_fase2_show, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown("### 🔹 FONDEADO")
    df_fondeado_show = pd.DataFrame([
        {"Concepto Principal": "Tamaño Cuenta Fondeada", "Monto 1 ($)": f"${tam_challenge:,.2f}", "Concepto Secundario": "Gasto Acumulado Exness", "Monto 2 ($)": f"${total_gasto_exness_acum:,.2f}"},
        {"Concepto Principal": "Máximo Loss Lucid", "Monto 1 ($)": f"${drawdown_val:,.2f}", "Concepto Secundario": "Meta 1 A 2 (Objetivo)", "Monto 2 ($)": f"${meta_1a2:,.2f}"},
        {"Concepto Principal": "Colchón Requerido (X3)", "Monto 1 ($)": f"${total_gasto_exness_acum:,.2f}", "Concepto Secundario": "Total Colchón Generado", "Monto 2 ($)": f"${colchon_974:,.2f}"}
    ])
    st.dataframe(df_fondeado_show, use_container_width=True, hide_index=True)

    st.divider()

    st.markdown(f"### 🟡 UNA VEZ SE HAGA EL COLCHÓN SE DIVIDE LOS ${colchon_974:,.2f} EN 20 TRADES")
    
    c_stop1, c_stop2 = st.columns(2)
    max_stop_profit = c_stop1.number_input("Máximo Stop Profit Lucid ($)", value=150.0, step=10.0)
    max_stop_loss = c_stop2.number_input("Máximo Stop Loss Exness / Cobertura ($)", value=49.0, step=5.0)

    num_trades_profit = 4
    num_trades_loss = 4

    subtotal_profit = max_stop_profit * num_trades_profit
    subtotal_loss = max_stop_loss * num_trades_loss

    total_profit_lucid = meta_1a2 + subtotal_profit
    total_loss_exness = colchon_974 + subtotal_loss

    mitad_profit_lucid = total_profit_lucid / 2.0
    noventa_pct_trader = mitad_profit_lucid * 0.90
    neto_final_trader = noventa_pct_trader - total_loss_exness

    df_colchon_show = pd.DataFrame([
        {"Concepto": "MÁXIMO STOP LUCID", "Monto ($)": f"${max_stop_profit:,.2f}", "Trades": f"{num_trades_profit} TRADES", "Subtotal ($)": f"${subtotal_profit:,.2f}", "Resultado": "TOTAL PROFIT LUCID", "Total ($)": f"${total_profit_lucid:,.2f}"},
        {"Concepto": "MÁXIMO STOP EXNESS", "Monto ($)": f"${max_stop_loss:,.2f}", "Trades": f"{num_trades_loss} TRADES", "Subtotal ($)": f"${subtotal_profit:,.2f}", "Resultado": "TOTAL LOSS EXNESS (Cobertura)", "Total ($)": f"${total_loss_exness:,.2f}"}
    ])
    st.dataframe(df_colchon_show, use_container_width=True, hide_index=True)

    st.markdown("### 💰 Reparto Final & Cobertura Neta")
    
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Total Profit Lucid", f"${total_profit_lucid:,.2f}")
    r2.metric("50% Reparto / 90% Trader", f"${noventa_pct_trader:,.2f}")
    r3.metric("Cobertura Exness (-)", f"-${total_loss_exness:,.2f}")
    r4.metric("Neto Final para el Trader", f"${neto_final_trader:,.2f}")

    st.success(
        f"📋 **Desglose Explicativo del Neto Trader:**\n\n"
        f"1. **Total Profit Lucid:** `${total_profit_lucid:,.2f}`\n"
        f"2. **Mitad de la Empresa (50%):** `${mitad_profit_lucid:,.2f}`\n"
        f"3. **Ganancia Bruta Trader (90%):** `${noventa_pct_trader:,.2f}`\n"
        f"4. **Resta Cobertura Exness:** `${noventa_pct_trader:,.2f}` - `${total_loss_exness:,.2f}`\n\n"
        f"✅ **TOTAL NETO QUE QUEDA PARA TI:** **${neto_final_trader:,.2f}**"
    )

# --- TAB 5: CONFIGURACIÓN ---
with tab_config:
    st.subheader("⚙️ Ajustes del Sistema & Personalización")
    
    if st.button("🔄 Restablecer Confirmaciones por Defecto"):
        st.session_state["checklist_custom"] = REGLAS_DEFECTO.copy()
        st.success("Confirmaciones restablecidas a la lista original.")
        st.rerun()

    nueva_regla = st.text_input("Nueva confirmación:")
    if st.button("➕ Agregar Confirmación"):
        if nueva_regla.strip():
            st.session_state["checklist_custom"].append(nueva_regla.strip())
            st.rerun()

    for idx, item_texto in enumerate(st.session_state["checklist_custom"]):
        col_del1, col_del2 = st.columns([0.8, 0.2])
        col_del1.caption(f"• {item_texto}")
        if col_del2.button("❌", key=f"del_cfg_{idx}"):
            st.session_state["checklist_custom"].pop(idx)
            st.rerun()