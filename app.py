import streamlit as st
import pandas as pd
import sqlite3
import os
import calendar
from datetime import datetime, date

# Configuración de la pantalla
st.set_page_config(page_title="Trading Journal Pro", layout="wide", initial_sidebar_state="expanded")

# Carpeta para guardar las imágenes de los trades
OS_IMG_DIR = "imagenes_trades"
if not os.path.exists(OS_IMG_DIR):
    os.makedirs(OS_IMG_DIR)

# Conexión a la base de datos
conn = sqlite3.connect("trading_journal.db", check_same_thread=False)
c = conn.cursor()

# Crear tablas
c.execute('''
    CREATE TABLE IF NOT EXISTS trades (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        pnl REAL,
        num_trades INTEGER,
        confirmaciones TEXT,
        foto_antes TEXT,
        foto_despues TEXT,
        notas TEXT
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS checklist_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        texto TEXT NOT NULL
    )
''')

c.execute('''
    CREATE TABLE IF NOT EXISTS configuracion (
        id INTEGER PRIMARY KEY,
        capital_inicial REAL DEFAULT 50000.0,
        color_ganancia TEXT DEFAULT '#2ec4b6',
        color_perdida TEXT DEFAULT '#e63946'
    )
''')

# Garantizar compatibilidad con columnas de color
try:
    c.execute("ALTER TABLE configuracion ADD COLUMN color_ganancia TEXT DEFAULT '#2ec4b6'")
except sqlite3.OperationalError:
    pass

try:
    c.execute("ALTER TABLE configuracion ADD COLUMN color_perdida TEXT DEFAULT '#e63946'")
except sqlite3.OperationalError:
    pass

# Insertar configuración por defecto de forma segura
try:
    c.execute("INSERT OR IGNORE INTO configuracion (id, capital_inicial, color_ganancia, color_perdida) VALUES (1, 50000.0, '#2ec4b6', '#e63946')")
except sqlite3.OperationalError:
    c.execute("INSERT OR IGNORE INTO configuracion (id, capital_inicial) VALUES (1, 50000.0)")

conn.commit()

# --- LISTA DE CONFIRMACIONES PREDETERMINADAS ---
reglas_defecto = [
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

# Reiniciar reglas por defecto si la base de datos no contiene items
c.execute("SELECT COUNT(*) FROM checklist_items")
if c.fetchone()[0] == 0:
    for r in reglas_defecto:
        c.execute("INSERT INTO checklist_items (texto) VALUES (?)", (r,))
    conn.commit()

# --- DATOS GENERALES Y MÉTRICAS ---
df_all = pd.read_sql_query("SELECT * FROM trades ORDER BY fecha ASC", conn)
c.execute("SELECT capital_inicial, color_ganancia, color_perdida FROM configuracion WHERE id = 1")
cfg = c.fetchone()

if cfg:
    capital_inicial = cfg[0] if cfg[0] is not None else 50000.0
    color_ganancia = cfg[1] if (len(cfg) > 1 and cfg[1] is not None) else '#2ec4b6'
    color_perdida = cfg[2] if (len(cfg) > 2 and cfg[2] is not None) else '#e63946'
else:
    capital_inicial, color_ganancia, color_perdida = 50000.0, '#2ec4b6', '#e63946'

total_pnl = df_all['pnl'].sum() if not df_all.empty else 0.0
balance_final = capital_inicial + total_pnl
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
m1.metric("Capital Inicial", f"${capital_inicial:,.2f}")
m2.metric("Net Profit / Loss", f"${total_pnl:,.2f}", delta=f"{total_pnl:,.2f}")
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
            df_all['pnl_acumulado'] = df_all['pnl'].cumsum() + capital_inicial
            st.line_chart(df_all.set_index('fecha')['pnl_acumulado'])
        else:
            st.info("Registra trades para visualizar la curva de rendimiento.")

# --- TAB 2: CALENDARIO ---
with tab_cal:
    st.subheader("📅 Calendario Mensual de Resultados")
    col_m, col_y = st.columns(2)
    mes_sel = col_m.selectbox("Mes", list(range(1, 13)), index=datetime.now().month - 1)
    anio_sel = col_y.number_input("Año", value=datetime.now().year)

    query = "SELECT fecha, SUM(pnl) as total_pnl, SUM(num_trades) as total_trades FROM trades WHERE fecha LIKE ? GROUP BY fecha"
    df_trades_m = pd.read_sql_query(query, conn, params=(f"{anio_sel}-{mes_sel:02d}-%",))
    dict_trades = df_trades_m.set_index('fecha').to_dict(orient='index') if not df_trades_m.empty else {}

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
                    pnl_val = dict_trades[f_key]['total_pnl']
                    cnt_trades = dict_trades[f_key]['total_trades']
                    
                    selected_color = color_ganancia if pnl_val >= 0 else color_perdida
                    
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

        # --- SECTOR DE REGISTRO RÁPIDO DE PNL ---
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
        c.execute("SELECT texto FROM checklist_items")
        reglas_disponibles = [r[0] for r in c.fetchall()]

        respuestas_checklist = []
        for idx, regla in enumerate(reglas_disponibles):
            if st.checkbox(regla, key=f"chk_tab_{idx}"):
                respuestas_checklist.append(regla)

        st.markdown("**🖼️ Captura ANTES del Trade**")
        url_antes = st.text_input("Pegar Link TradingView (ANTES):", placeholder="https://www.tradingview.com/x/...")
        file_antes = st.file_uploader("O subir archivo de imagen (ANTES)", type=["png", "jpg", "jpeg"], key="tab_antes")

        st.markdown("**🖼️ Captura DESPUÉS del Trade**")
        url_despues = st.text_input("Pegar Link TradingView (DESPUÉS):", placeholder="https://www.tradingview.com/x/...")
        file_despues = st.file_uploader("O subir archivo de imagen (DESPUÉS)", type=["png", "jpg", "jpeg"], key="tab_despues")

        notas_input = st.text_area("Notas / Lecciones del día")

        if st.button("💾 Guardar en Bitácora", use_container_width=True):
            path_antes = ""
            if url_antes.strip():
                path_antes = url_antes.strip()
            elif file_antes:
                path_antes = os.path.join(OS_IMG_DIR, f"{fecha_str}_antes_{file_antes.name}")
                with open(path_antes, "wb") as f:
                    f.write(file_antes.getbuffer())

            path_despues = ""
            if url_despues.strip():
                path_despues = url_despues.strip()
            elif file_despues:
                path_despues = os.path.join(OS_IMG_DIR, f"{fecha_str}_despues_{file_despues.name}")
                with open(path_despues, "wb") as f:
                    f.write(file_despues.getbuffer())

            confirmaciones_str = " | ".join(respuestas_checklist)

            c.execute('''
                INSERT INTO trades (fecha, pnl, num_trades, confirmaciones, foto_antes, foto_despues, notas)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (fecha_str, pnl_input, trades_count, confirmaciones_str, path_antes, path_despues, notas_input))
            conn.commit()
            st.success("✅ Trade registrado correctamente.")
            st.rerun()

    with c_insp:
        st.subheader("🔍 Detalle del Día")
        fecha_consulta = st.date_input("Seleccionar fecha", date.today(), key="consulta_tab")
        f_consulta_str = fecha_consulta.strftime("%Y-%m-%d")

        c.execute("SELECT id, fecha, pnl, num_trades, confirmaciones, foto_antes, foto_despues, notas FROM trades WHERE fecha = ?", (f_consulta_str,))
        registros = c.fetchall()

        if registros:
            for r in registros:
                st.markdown(f"### Trade #{r[0]} - PnL: **${r[2]:,.2f}**")
                st.write(f"**Trades tomados:** {r[3]}")
                
                confirmaciones_hechas = r[4].split(" | ") if r[4] else []
                st.write(f"**Confirmaciones cumplidas ({len(confirmaciones_hechas)}):**")
                for conf in confirmaciones_hechas:
                    if conf:
                        st.caption(f"✓ {conf}")

                if r[7]:
                    st.info(f"**Notas:** {r[7]}")
                
                col_img1, col_img2 = st.columns(2)
                
                if r[5]:
                    if r[5].startswith("http"):
                        col_img1.image(r[5], caption="Antes del Trade (Link TradingView)", use_container_width=True)
                    elif os.path.exists(r[5]):
                        col_img1.image(r[5], caption="Antes del Trade", use_container_width=True)

                if r[6]:
                    if r[6].startswith("http"):
                        col_img2.image(r[6], caption="Después del Trade (Link TradingView)", use_container_width=True)
                    elif os.path.exists(r[6]):
                        col_img2.image(r[6], caption="Después del Trade", use_container_width=True)

                st.divider()
        else:
            st.warning("No hay registros en esta fecha.")

# --- TAB 4: BALANZAS 2.0 (CON LÓGICA DE COBERTURA Y PAGO NETO VINCULADA) ---
with tab_bal:
    st.subheader("⚖️ Hoja Balanzas 2.0 (Calculadora de Cobertura Lucid / Exness)")
    st.caption("Los valores de las tablas se recalculan automáticamente en cadena cuando modificas los parámetros de entrada.")

    # 1. PARÁMETROS DE ENTRADA EDITABLES
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

    # 2. CÁLCULOS MATEMÁTICOS VINCULADOS EN CADENA
    drawdown_val = tam_challenge * drawdown_pct
    total_target = req1 + req2
    
    # FASE 1
    riesgo_fase1 = costo_lucid * rr_ratio
    factor_fase1 = (costo_lucid / riesgo_fase1) if riesgo_fase1 > 0 else 0
    riesgo_max_dd1 = drawdown_val * rr_ratio
    pct_riesgo_tiro1 = (req1 / tam_challenge) if tam_challenge > 0 else 0

    # FASE 2
    gasto_fase1 = riesgo_fase1
    total_gasto_fase2 = gasto_fase1 + costo_lucid
    riesgo_fase2 = total_gasto_fase2 * rr_ratio
    factor_fase2 = (costo_lucid / riesgo_fase1) if riesgo_fase1 > 0 else 0
    riesgo_max_dd2 = drawdown_val * rr_ratio

    # FONDEADO
    total_gasto_exness_acum = total_gasto_fase2 + riesgo_fase2
    meta_1a2 = drawdown_val * 2
    colchon_974 = total_gasto_exness_acum * 3

    st.divider()

    # --- TABLA SUPERIOR ENCABEZADO ---
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

    # --- SECCIÓN PRIMERA FASE 1 ---
    st.markdown("### 🔹 PRIMERA FASE 1")
    df_fase1_show = pd.DataFrame([
        {"Base ($)": f"${costo_lucid:,.2f}", "RR": f"{rr_ratio:.2f}", "Riesgo por Tiro ($)": f"${riesgo_fase1:,.2f}", "Factor / Pct": f"{factor_fase1:.3f}", "Descripción": "Porcentaje de riesgo por tiro"},
        {"Base ($)": f"${drawdown_val:,.2f}", "RR": f"{rr_ratio:.2f}", "Riesgo por Tiro ($)": f"${riesgo_max_dd1:,.2f}", "Factor / Pct": f"{pct_riesgo_tiro1*100:.2f}%", "Descripción": "Porcentaje de riesgo por tiro"}
    ])
    st.dataframe(df_fase1_show, use_container_width=True, hide_index=True)

    st.divider()

    # --- SECCIÓN SEGUNDA FASE 2 ---
    st.markdown("### 🔹 SEGUNDA FASE 2")
    st.caption("📌 *Se suma la pérdida del primer trade más la cuenta de fondeo*")
    
    df_fase2_show = pd.DataFrame([
        {"Concepto / Base": "Cálculo Gasto Exness", "Gasto Inicial ($)": f"${gasto_fase1:,.2f}", "Costo Fondeo ($)": f"${costo_lucid:,.2f}", "Total Gasto Exness ($)": f"${total_gasto_fase2:,.2f}", "RR": "-", "Riesgo Calculado ($)": "-"},
        {"Concepto / Base": "Riesgo sobre Gasto", "Gasto Inicial ($)": "-", "Costo Fondeo ($)": "-", "Total Gasto Exness ($)": f"${total_gasto_fase2:,.2f}", "RR": f"{rr_ratio:.2f}", "Riesgo Calculado ($)": f"${riesgo_fase2:,.2f}"},
        {"Concepto / Base": "Riesgo sobre Drawdown", "Gasto Inicial ($)": "-", "Costo Fondeo ($)": "-", "Total Gasto Exness ($)": f"${drawdown_val:,.2f}", "RR": f"{rr_ratio:.2f}", "Riesgo Calculado ($)": f"${riesgo_max_dd2:,.2f}"}
    ])
    st.dataframe(df_fase2_show, use_container_width=True, hide_index=True)

    st.divider()

    # --- SECCIÓN FONDEADO ---
    st.markdown("### 🔹 FONDEADO")
    df_fondeado_show = pd.DataFrame([
        {"Concepto Principal": "Tamaño Cuenta Fondeada", "Monto 1 ($)": f"${tam_challenge:,.2f}", "Concepto Secundario": "Gasto Acumulado Exness", "Monto 2 ($)": f"${total_gasto_exness_acum:,.2f}"},
        {"Concepto Principal": "Máximo Loss Lucid", "Monto 1 ($)": f"${drawdown_val:,.2f}", "Concepto Secundario": "Meta 1 A 2 (Objetivo)", "Monto 2 ($)": f"${meta_1a2:,.2f}"},
        {"Concepto Principal": "Colchón Requerido (X3)", "Monto 1 ($)": f"${total_gasto_exness_acum:,.2f}", "Concepto Secundario": "Total Colchón Generado", "Monto 2 ($)": f"${colchon_974:,.2f}"}
    ])
    st.dataframe(df_fondeado_show, use_container_width=True, hide_index=True)

    st.divider()

    # --- SECCIÓN COLCHÓN, COBERTURA Y REPARTO NETO ---
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
        {"Concepto": "MÁXIMO STOP EXNESS", "Monto ($)": f"${max_stop_loss:,.2f}", "Trades": f"{num_trades_loss} TRADES", "Subtotal ($)": f"${subtotal_loss:,.2f}", "Resultado": "TOTAL LOSS EXNESS (Cobertura)", "Total ($)": f"${total_loss_exness:,.2f}"}
    ])
    st.dataframe(df_colchon_show, use_container_width=True, hide_index=True)

    # --- PANEL RESUMEN LÍQUIDO DEL TRADER ---
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
    
    st.markdown("### 🎨 Personalización de Colores de PnL")
    col_c1, col_c2 = st.columns(2)
    nuevo_col_win = col_c1.color_picker("Color para Días Ganadores", value=color_ganancia)
    nuevo_col_loss = col_c2.color_picker("Color para Días Perdedores", value=color_perdida)
    
    if st.button("💾 Guardar Colores"):
        c.execute("UPDATE configuracion SET color_ganancia = ?, color_perdida = ? WHERE id = 1", (nuevo_col_win, nuevo_col_loss))
        conn.commit()
        st.success("Colores actualizados correctamente.")
        st.rerun()

    st.divider()
    st.markdown("### 💰 Capital Inicial")
    nuevo_capital = st.number_input("Configurar Capital de la Cuenta ($)", value=float(capital_inicial), step=1000.0)
    if st.button("Guardar Capital"):
        c.execute("UPDATE configuracion SET capital_inicial = ? WHERE id = 1", (nuevo_capital,))
        conn.commit()
        st.success("Capital actualizado.")
        st.rerun()

    st.divider()
    st.markdown("### 🛠️ Editar Reglas del Checklist")
    
    if st.button("🔄 Restablecer Confirmaciones por Defecto"):
        c.execute("DELETE FROM checklist_items")
        for r in reglas_defecto:
            c.execute("INSERT INTO checklist_items (texto) VALUES (?)", (r,))
        conn.commit()
        st.success("Confirmaciones restablecidas a la lista original.")
        st.rerun()

    nueva_regla = st.text_input("Nueva confirmación:")
    if st.button("➕ Agregar Confirmación"):
        if nueva_regla.strip():
            c.execute("INSERT INTO checklist_items (texto) VALUES (?)", (nueva_regla.strip(),))
            conn.commit()
            st.rerun()

    c.execute("SELECT id, texto FROM checklist_items")
    items_actuales = c.fetchall()
    for item_id, item_texto in items_actuales:
        col_del1, col_del2 = st.columns([0.8, 0.2])
        col_del1.caption(f"• {item_texto}")
        if col_del2.button("❌", key=f"del_cfg_{item_id}"):
            c.execute("DELETE FROM checklist_items WHERE id = ?", (item_id,))
            conn.commit()
            st.rerun()