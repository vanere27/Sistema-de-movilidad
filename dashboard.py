import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
from datetime import datetime

# ================= CONFIGURACIÓN DE PÁGINA =================
st.set_page_config(
    page_title="Monitor de Aforo",
    page_icon="📊",
    layout="wide"
)

# Título y Auto-refresco
st.title("📊 Dashboard de Control de Ingresos y Salidas")
st.markdown("---")

# ================= FUNCIÓN DE CARGA DE DATOS =================
def cargar_datos():
    # Conectar a la base de datos
    try:
        conn = sqlite3.connect('registro_personas.db')
        # Leemos todo
        query = "SELECT * FROM conteos"
        df = pd.read_sql(query, conn)
        conn.close()

        if df.empty:
            return pd.DataFrame()

        # Crear columna completa de Fecha-Hora
        # Asumiendo que tus columnas se llaman 'fecha' (YYYY-MM-DD) y 'hora' (HH:MM:SS)
        df['timestamp'] = pd.to_datetime(df['fecha'] + ' ' + df['hora'])
        
        # Extraer componentes útiles para filtros
        df['Año'] = df['timestamp'].dt.year
        df['Mes'] = df['timestamp'].dt.month_name()
        df['Dia'] = df['timestamp'].dt.date
        df['Hora'] = df['timestamp'].dt.hour
        
        return df
    except Exception as e:
        st.error(f"Error al leer la base de datos: {e}")
        return pd.DataFrame()

# Cargar datos
df = cargar_datos()

# ================= BARRA LATERAL (FILTROS) =================
st.sidebar.header("Filtros")

if not df.empty:
    # Filtro de Fecha
    min_date = df['Dia'].min()
    max_date = df['Dia'].max()
    
    fecha_inicio = st.sidebar.date_input("Fecha Inicio", min_date)
    fecha_fin = st.sidebar.date_input("Fecha Fin", max_date)

    # Filtrar el DataFrame
    mask = (df['Dia'] >= fecha_inicio) & (df['Dia'] <= fecha_fin)
    df_filtrado = df.loc[mask]
else:
    st.warning("⚠️ No hay datos en la base de datos todavía. Enciende el sistema de conteo.")
    df_filtrado = df

# ================= KPIs (INDICADORES CLAVE) =================
if not df_filtrado.empty:
    col1, col2, col3 = st.columns(3)

    total_entradas = len(df_filtrado[df_filtrado['tipo'] == 'ENTRADA'])
    total_salidas = len(df_filtrado[df_filtrado['tipo'] == 'SALIDA'])
    # Aforo actual (Neto)
    aforo_actual = total_entradas - total_salidas

    col1.metric("Total Entradas", total_entradas, delta="Selección")
    col2.metric("Total Salidas", total_salidas, delta="-Selección", delta_color="inverse")
    col3.metric("Aforo Neto (Ocupación)", aforo_actual, delta="Personas dentro")

    st.markdown("---")

    # ================= PESTAÑAS DE ANÁLISIS =================
    tab1, tab2, tab3 = st.tabs(["📈 Por Hora", "📅 Por Día", "🗓️ Mensual/Anual"])

    with tab1:
        st.subheader("Comportamiento por Hora")
        # Agrupar por hora y tipo
        df_hora = df_filtrado.groupby(['Hora', 'tipo']).size().reset_index(name='Conteo')
        
        fig_hora = px.bar(df_hora, x='Hora', y='Conteo', color='tipo', 
                          barmode='group', title="Entradas vs Salidas por Hora",
                          color_discrete_map={'ENTRADA': '#00CC96', 'SALIDA': '#EF553B'})
        st.plotly_chart(fig_hora, use_container_width=True)

    with tab2:
        st.subheader("Evolución Diaria")
        df_dia = df_filtrado.groupby(['Dia', 'tipo']).size().reset_index(name='Conteo')
        
        fig_dia = px.line(df_dia, x='Dia', y='Conteo', color='tipo', 
                          markers=True, title="Tendencia Diaria",
                          color_discrete_map={'ENTRADA': '#00CC96', 'SALIDA': '#EF553B'})
        st.plotly_chart(fig_dia, use_container_width=True)

    with tab3:
        col_mes, col_anio = st.columns(2)
        
        with col_mes:
            st.subheader("Totales por Mes")
            df_mes = df_filtrado.groupby(['Mes', 'tipo']).size().reset_index(name='Conteo')
            fig_mes = px.pie(df_filtrado, names='tipo', title="Distribución Total",
                             color_discrete_map={'ENTRADA': '#00CC96', 'SALIDA': '#EF553B'})
            st.plotly_chart(fig_mes, use_container_width=True)

        with col_anio:
            st.subheader("Tabla de Datos Recientes")
            st.dataframe(df_filtrado[['fecha', 'hora', 'tipo', 'track_id']].sort_values(by=['fecha', 'hora'], ascending=False).head(10))

    # ================= DESCARGAR DATOS =================
    st.markdown("### 📥 Descargar Reporte")
    csv = df_filtrado.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Descargar datos en CSV (Excel)",
        data=csv,
        file_name='reporte_aforo.csv',
        mime='text/csv',
    )

else:
    st.info("Esperando datos... Camina frente a la cámara para generar registros.")