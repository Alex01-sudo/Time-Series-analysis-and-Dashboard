import streamlit as st
import pandas as pd
import joblib
import plotly.graph_objects as go

st.set_page_config(page_title="Simulazione Forecast", layout="wide")

st.title("🔮 Simulazione Forecasting in Tempo Reale")
st.markdown("Scorri la linea temporale per generare previsioni basate sui dati storici di input.")

# ==============================================================================
# 1. CONTROLLO DATI CONDIVISI
# ==============================================================================
if 'df_condiviso' not in st.session_state:
    st.warning("⚠️ Non hai caricato i dati storici!")
    st.info("Torna alla pagina principale (Home) e carica il file CSV.")
    st.stop()

df = st.session_state['df_condiviso'].copy()

# ==============================================================================
# 2. CARICAMENTO MODELLO
# ==============================================================================
with st.sidebar:
    st.header("Configurazione")
    model_file = st.file_uploader("Carica Modello (.joblib)", type=["joblib"])

model = None
if model_file:
    try:
        model = joblib.load(model_file)
        st.success("Modello pronto per il forecast.")
    except Exception as e:
        st.error(f"Errore caricamento: {e}")

# ==============================================================================
# 3. PREPARAZIONE DATI (FILTRO DICEMBRE 2012)
# ==============================================================================
col_data = df.columns[0] # Assumiamo la prima colonna sia la data
try:
    df[col_data] = pd.to_datetime(df[col_data])
except Exception as e:
    st.error(f"Impossibile convertire '{col_data}' in date.")
    st.stop()

# Range richiesto
start_date = "2012-12-01"
end_date = "2013-01-01"

# Filtriamo il dataset per il mese di test
mask = (df[col_data] >= start_date) & (df[col_data] < end_date)
df_test = df.loc[mask].sort_values(by=col_data).reset_index(drop=True)

if df_test.empty:
    st.error("Nessun dato trovato nel range Dicembre 2012.")
    st.stop()

# ==============================================================================
# 4. INTERFACCIA: SLIDER TEMPORALE
# ==============================================================================
if model is not None:
    st.subheader("🗓️ Seleziona il momento della previsione")
    
    # Lista date formattate
    opzioni_date = df_test[col_data].dt.strftime('%Y-%m-%d %H:%M:%S').tolist()
    
    # Slider
    data_selezionata_str = st.select_slider(
        "Spostati nel tempo:",
        options=opzioni_date,
        value=opzioni_date[0] # Parte dall'inizio
    )
    
    # Troviamo la riga corrispondente alla selezione
    riga_selezionata = df_test[df_test[col_data].astype(str) == data_selezionata_str]
    
    if not riga_selezionata.empty:
        # ==========================================================================
        # 5. ESECUZIONE PREDIZIONE
        # ==========================================================================
        
        # Gestione input modello
        if hasattr(model, 'feature_names_in_'):
            cols_modello = model.feature_names_in_
            
            # Verifica colonne
            missing = [c for c in cols_modello if c not in riga_selezionata.columns]
            
            if not missing:
                # Dati di input per il modello
                X_input = riga_selezionata[cols_modello]
                
                # PREDIZIONE
                predizione = model.predict(X_input)[0]
                
                # --- VISUALIZZAZIONE KPI ---
                st.markdown("### Risultato Forecast")
                c1, c2, c3 = st.columns(3)
                c1.info(f"📅 Data: {data_selezionata_str}")
                # Mostriamo la predizione in grande
                c2.metric("Noleggi Previsti (cnt)", f"{predizione:.0f}")
                
                # Mostriamo un parametro chiave di input (es. Temp) per contesto
                temp_val = riga_selezionata['temp'].values[0] if 'temp' in riga_selezionata.columns else 0
                c3.metric("Temperatura Input", f"{temp_val:.2f}")

                st.markdown("---")
                
                # ==========================================================================
                # 6. GRAFICO SIMULAZIONE (STORICO + PREVISIONE)
                # ==========================================================================
                
                # Prendiamo i dati storici FINO alla data selezionata (escluso il futuro)
                # Così simuliamo di non sapere cosa succede dopo
                data_corrente_dt = pd.to_datetime(data_selezionata_str)
                df_history = df_test[df_test[col_data] <= data_corrente_dt]
                
                fig = go.Figure()

                # 1. Linea dello STORICO (quello che è "già successo" fino ad ora)
                fig.add_trace(go.Scatter(
                    x=df_history[col_data],
                    y=df_history['cnt'],
                    mode='lines',
                    name='Storico Acquisito',
                    line=dict(color='rgba(0,100,250, 0.5)', width=2)
                ))

                # 2. Punto della PREVISIONE ATTUALE
                fig.add_trace(go.Scatter(
                    x=[data_corrente_dt],
                    y=[predizione],
                    mode='markers',
                    name='Forecast Modello',
                    marker=dict(color='red', size=15, symbol='star', line=dict(width=2, color='black'))
                ))

                fig.update_layout(
                    title="Monitoraggio Previsione",
                    xaxis_title="Tempo",
                    yaxis_title="Valore cnt",
                    xaxis_range=[pd.to_datetime(start_date), pd.to_datetime(end_date)], # Asse X fisso per tutto il mese
                    yaxis_range=[0, df_test['cnt'].max() * 1.2], # Asse Y fisso per stabilità
                    showlegend=True
                )

                st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.error(f"Mancano colonne nel CSV: {missing}")
        else:
            st.error("Il modello non ha i nomi delle feature salvati.")

else:
    st.info("👈 Carica il modello nella sidebar per iniziare la simulazione.")