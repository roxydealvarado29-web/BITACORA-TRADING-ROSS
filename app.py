Trader", f"${noventa_pct_trader:,.2f}")    r3.metric("Cobertura Exness (-)", f"-$
{total
_loss_exness:,.2f}")    r4.metric("Neto Final para el Trader", f"${neto_fina

l_trader:,.2f}")    st.success(        f"📋 **Desglose E
xpli
cativo del Neto Trader:**\n\n"    
    f"1. Total Profit Lucid: `${total_profit_lucid:,.2f}`\n"  
      f"2. Mitad de la Empresa (50%): `${mitad_profit_lucid:,.2f}`\n
"        f"3. Ganancia Bruta Trader (90%): `${noventa_pct_trader
:,.2f}`\n"        f"4. Resta Cobertura Exness: `${noventa_pct_trader

:,.2f}` - `${to
tal_loss_exness:,.2f}`\n\n"        f"✅ **TOTAL NETO QUE QUE
DA PARA TI:** **${neto_final_trader:,.2f}**"    )# --- TAB 5: CONFIG
URACIÓN ---with tab_config:    st.subheader("⚙️ Ajustes del Sistema & Perso
nalización")        if st.button("🔄 Restablecer Confirmaciones por Defecto")
:        st.session_state["checklist_custom"] = REGLAS_DEFECTO.copy()        st.success("Confirmaciones 
restablecidas a la lista original.")        st.rerun()    nueva_regla = st.t
ext_i

nput("Nueva confirmación:")   
 if st.button("➕
 Agregar Confirmación"):        if nueva_regla.strip():     
    
   st.session_state["checklist_custom"].append(nueva_regla.str
ip())            st.rerun()    for idx, item_texto in enumerate(st.s
ession_state["checklist_custom"]):        col_del1, col_del2 = st.colum
ns([0.8, 0.2])    

    col_del1.caption(f"• {item_texto}")        if col_
del2.button("❌", key=f"del_cfg_{idx}"):    
        st.session_state["check
list_custom"].pop(idx)            st.rerun()