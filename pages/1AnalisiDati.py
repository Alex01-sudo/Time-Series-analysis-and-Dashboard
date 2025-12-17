import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Configurazione pagina
st.set_page_config(page_title="Analisi Serie Storica", layout="wide")

# Titolo
st.title("📊 Analisi Serie Storica & KPI Business")

st.sidebar.header("1. Carica i Dati (CSV)")
uploaded_file = st.sidebar.file_uploader("File dati storici (CSV)", type=["csv"])

# --- CARICAMENTO DATI ---
if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file)
        
        # Conversione data se esiste colonna 'dteday' (comune in questi dataset)
        if 'dteday' in df.columns:
            df['dteday'] = pd.to_datetime(df['dteday'])
            
        st.session_state['df_condiviso'] = df
        st.sidebar.success("Dati caricati correttamente!")
    except Exception as e:
        st.sidebar.error(f"Errore nel caricamento: {e}")

# --- ANALISI ---
if 'df_condiviso' in st.session_state:
    df = st.session_state['df_condiviso']
    
    # ---------------------------------------------------------
    # SEZIONE 1: PANORAMICA (Tuo codice originale)
    # ---------------------------------------------------------
    st.write(f"Dataset caricato: {len(df)} righe.")
    
    with st.expander("Visualizza Anteprima Dati e Statistiche Base", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Righe:** {len(df)}")
            st.write(f"**Colonne:** {len(df.columns)}")
        with col2:
            st.write("**Colonne disponibili:**", df.columns.tolist())

        st.dataframe(df.head())

        # Statistiche rapide
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Media Totale (cnt)", f"{df['cnt'].mean():.0f}")
        c2.metric("Min", f"{df['cnt'].min()}")
        c3.metric("Max", f"{df['cnt'].max()}")
        c4.metric("Std Dev", f"{df['cnt'].std():.0f}")

    st.markdown("---")

    # ---------------------------------------------------------
    # SEZIONE 2: KPI & SUPPORTO DECISIONI (Index Date + OHE)
    # ---------------------------------------------------------
  
    st.header("🚀 KPI & Supporto alle Decisioni")

    # Nomi colonne
    col_registered = 'registered' 
    col_total = 'cnt'
    # Colonne Meteo One-Hot (in ordine di bontà)
    cols_meteo_ohe = ['weathersit_1.0', 'weathersit_2.0', 'weathersit_3.0', 'weathersit_4.0']

    if col_registered in df.columns and col_total in df.columns:
        
       # --- 0. PREPARAZIONE INDICE (CORRETTO) ---
        # Ci assicuriamo che l'indice sia datetime.
        try:
            # 1. Impostiamo la prima colonna come indice (datetime)
            df.index = pd.to_datetime(df.iloc[:, 0])
            
            # 2. Rinominiamo l'indice per evitare nomi generici come "Unnamed: 0"
            df.index.name = 'Date_Index'
            
            # 3. RIMUOVIAMO la prima colonna dai dati per evitare duplicati/ambiguità
            #    (Selezioniamo tutte le righe e tutte le colonne dalla seconda in poi)
            df = df.iloc[:, 1:] 
            
        except Exception as e:
            st.error(f"Errore nella gestione dell'indice: {e}")

        # --- 1. AGGREGAZIONE GIORNALIERA (Tramite Indice appena settato) ---
        # Raggruppiamo sommando i volumi usando la data dell'indice
        # df.index.date prende solo la parte "YYYY-MM-DD" ignorando l'ora
        df_daily = df.groupby(df.index.date)[[col_registered, col_total]].sum()
        
        # Riconvertiamo l'indice del nuovo df_daily in datetime per sicurezza (per Plotly)
        df_daily.index = pd.to_datetime(df_daily.index)
        
        # Calcolo KPI Efficienza sui dati GIORNALIERI
        df_daily['kpi_efficiency_rate'] = (df_daily[col_registered] / df_daily[col_total]) * 100
        
        st.success(f"✅ Dati aggregati per giorno usando la prima colonna come data ({len(df_daily)} giorni trovati).")

        # --- 2. KPI CARDS ---
        kpi_avg = df_daily['kpi_efficiency_rate'].mean()
        kpi_last = df_daily['kpi_efficiency_rate'].iloc[-1]
        
        k1, k2 = st.columns(2)
        k1.metric("Efficienza Media Giornaliera", f"{kpi_avg:.1f}%")
        k2.metric("Efficienza Ultimo Giorno", f"{kpi_last:.1f}%", delta=f"{kpi_last - kpi_avg:.1f}%")

        # --- 3. GRAFICO MONITORAGGIO TEMPORALE ---
        st.subheader("📈 Trend Giornaliero: % Registrati")
        
        fig_kpi_time = go.Figure()
        
        fig_kpi_time.add_trace(go.Scatter(
            x=df_daily.index,  # Usiamo l'indice (le date) come asse X
            y=df_daily['kpi_efficiency_rate'],
            mode='lines', 
            name='% Registrati', 
            line=dict(color='#00CC96', width=2)
        ))
        
        fig_kpi_time.add_hline(y=kpi_avg, line_dash="dot", annotation_text="Media", line_color="red")
        
        fig_kpi_time.update_layout(
            title="Andamento Efficienza Business (Aggregato per Giorno)", 
            template="plotly_white", 
            yaxis_title="% Registrati",
            hovermode="x unified"
        )
        st.plotly_chart(fig_kpi_time, use_container_width=True)

                # --- 4. GESTIONE METEO (COMBO CHART + INSIGHT INTERATTIVO) ---
        cols_esistenti = [c for c in cols_meteo_ohe if c in df.columns]
        
        if len(cols_esistenti) > 0:
            st.subheader("🌤️ Impatto Meteo: Analisi Trend 2011 vs 2012")
            
            # --- SELETTORE METRICA ---
            scelta_utente = st.radio(
                "Scegli la tipologia di utenza da analizzare:",
                ["Totale (cnt)", "Registrati (registered)", "Occasionali (casual)"],
                horizontal=True,
                key="radio_weather_combo"
            )
            
            map_colonne = {
                "Totale (cnt)": "cnt",
                "Registrati (registered)": "registered",
                "Occasionali (casual)": "casual"
            }
            col_analizzata = map_colonne[scelta_utente]

            if col_analizzata not in df.columns:
                st.error(f"La colonna '{col_analizzata}' non è presente nel dataset.")
            else:
                # Preparazione Dati
                df_meteo = df.copy()
                df_meteo['Year'] = df_meteo.index.year
                df_meteo['Meteo_Raw'] = df_meteo[cols_esistenti].idxmax(axis=1)
                
                mapping_nomi = {
                    'weathersit_1.0': '1. Sole/Sereno',
                    'weathersit_2.0': '2. Nuvoloso',
                    'weathersit_3.0': '3. Pioggia Leggera',
                    'weathersit_4.0': '4. Tempesta'
                }
                df_meteo['Meteo_Label'] = df_meteo['Meteo_Raw'].map(mapping_nomi)
                
                # Raggruppamento
                df_weather_comp = df_meteo.groupby(['Year', 'Meteo_Label'])[col_analizzata].mean().reset_index()
                
                df_2011 = df_weather_comp[df_weather_comp['Year'] == 2011]
                df_2012 = df_weather_comp[df_weather_comp['Year'] == 2012]

                # --- COSTRUZIONE COMBO CHART ---
                fig_weather = go.Figure()

                # 2011: Barre + Linea
                fig_weather.add_trace(go.Bar(
                    x=df_2011['Meteo_Label'],
                    y=df_2011[col_analizzata],
                    name='2011 (Volume)',
                    marker_color='rgba(99, 110, 250, 0.5)', # Blu semi-trasparente
                    text=df_2011[col_analizzata].apply(lambda x: f"{x:.0f}"),
                    textposition='auto'
                ))
                fig_weather.add_trace(go.Scatter(
                    x=df_2011['Meteo_Label'],
                    y=df_2011[col_analizzata],
                    name='2011 (Trend)',
                    mode='lines+markers',
                    marker=dict(symbol='circle', size=8, color='#636EFA'),
                    line=dict(width=3, color='#636EFA')
                ))

                # 2012: Barre + Linea
                fig_weather.add_trace(go.Bar(
                    x=df_2012['Meteo_Label'],
                    y=df_2012[col_analizzata],
                    name='2012 (Volume)',
                    marker_color='rgba(239, 85, 59, 0.5)', # Rosso semi-trasparente
                    text=df_2012[col_analizzata].apply(lambda x: f"{x:.0f}"),
                    textposition='auto'
                ))
                fig_weather.add_trace(go.Scatter(
                    x=df_2012['Meteo_Label'],
                    y=df_2012[col_analizzata],
                    name='2012 (Trend)',
                    mode='lines+markers',
                    marker=dict(symbol='circle', size=8, color='#EF553B'),
                    line=dict(width=3, color='#EF553B')
                ))

                fig_weather.update_layout(
                    title=f"Analisi Trend Meteo: {scelta_utente}",
                    xaxis_title="Condizione Meteo",
                    yaxis_title=f"Media {scelta_utente}",
                    barmode='group',
                    template="plotly_white",
                    legend=dict(title="Anno/Tipo"),
                    hovermode="x unified"
                )
                
                st.plotly_chart(fig_weather, use_container_width=True)
                
                # --- INSIGHT INTERATTIVO ---
                st.markdown("#### 📉 Calcolo della Sensibilità al Meteo")
                
                # Selettore specifico per l'insight
                anno_insight = st.radio(
                    "Di quale anno vuoi calcolare il crollo della domanda (Sole vs Pioggia)?",
                    [2011, 2012],
                    horizontal=True,
                    key="radio_insight_year"
                )
                
                # Selezioniamo il dataframe dell'anno scelto
                df_target = df_2011 if anno_insight == 2011 else df_2012
                
                if not df_target.empty:
                    # Cerchiamo i valori specifici usando string matching parziale ('1.' per Sole, '3.' per Pioggia)
                    val_sole = df_target[df_target['Meteo_Label'].str.contains('1.')][col_analizzata].values
                    val_pioggia = df_target[df_target['Meteo_Label'].str.contains('4.')][col_analizzata].values
                    
                    if len(val_sole) > 0 and len(val_pioggia) > 0:
                        val_s = val_sole[0]
                        val_p = val_pioggia[0]
                        
                        if val_s > 0:
                            calo = ((val_s - val_p) / val_s) * 100
                            
                            # Creiamo un messaggio dinamico
                            st.info(f"""
                            💡 **Insight {anno_insight}:** Nel **{anno_insight}**, passando da condizioni ottimali (Sole) a tempesta, 
                            la domanda di **{scelta_utente}** crolla del **{calo:.1f}%**.
                            
                            * Media con Sole: **{val_s:.0f}**
                            * Media con Pioggia: **{val_p:.0f}**
                            """)
                        else:
                            st.warning("Il valore medio con il Sole è 0, impossibile calcolare la percentuale.")
                    else:
                        st.warning(f"Dati insufficienti nel {anno_insight} per confrontare Sole vs Pioggia.")
                else:
                    st.warning("Nessun dato disponibile per l'anno selezionato.")

        else:
            st.info("Nessuna colonna meteo trovata.")
    else:
        st.warning(f"Attenzione: Colonne '{col_registered}' o '{col_total}' non trovate.")
    # ---------------------------------------------------------
    # SEZIONE 3: ANALISI CORRELAZIONI (Tuo codice originale mantenuto)
    # ---------------------------------------------------------
    st.subheader("🔎 Analisi Approfondita (Filtri & Correlazioni)")
    
    # ... (Il resto del tuo codice originale per scatter e box plot)
    col_workday = 'workingday'
    if col_workday in df.columns:
        filtro_tipo = st.radio(
            "Filtra i dati per giorni lavorativi:",
            options=["Tutti i dati", "Giorni Lavorativi (1)", "Non Lavorativi (0)"],
            horizontal=True,
            key="filtro_workday" # Aggiunto key per evitare conflitti
        )
        if filtro_tipo == "Giorni Lavorativi (1)":
            df_filtrato = df[df[col_workday] == 1]
        elif filtro_tipo == "Non Lavorativi (0)":
            df_filtrato = df[df[col_workday] == 0]
        else:
            df_filtrato = df
    else:
        df_filtrato = df

    opzioni_analisi = ['hr', 'season', 'temp', 'hum', 'windspeed']
    opzioni_disponibili = [col for col in opzioni_analisi if col in df.columns]

    if opzioni_disponibili:
        variabile_x = st.selectbox("Scegli variabile X:", opzioni_disponibili, key="var_select")
        
        tab1, tab2 = st.tabs(["🔴 Scatter con Media", "📦 Box Plot"])
        
        with tab1:
            df_media = df_filtrato.groupby(variabile_x)['cnt'].mean().reset_index().sort_values(by=variabile_x)
            fig_scatter = px.scatter(df_filtrato, x=variabile_x, y="cnt", color="cnt", opacity=0.4, title=f"Scatter: {variabile_x} vs cnt")
            fig_scatter.add_scatter(x=df_media[variabile_x], y=df_media['cnt'], mode='markers', name='Media', marker=dict(color='red', size=10, symbol='diamond'))
            st.plotly_chart(fig_scatter, use_container_width=True)
            
        with tab2:
            fig_box = px.box(df_filtrato, x=variabile_x, y="cnt", color=variabile_x, title=f"Box Plot: {variabile_x}")
            fig_box.update_layout(showlegend=False)
            st.plotly_chart(fig_box, use_container_width=True)

else:
    st.info("👈 Carica un file CSV dalla barra laterale per iniziare.")