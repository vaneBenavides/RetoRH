import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path

# --- Configuración base de la página ---
st.set_page_config(page_title="Dashboard RR.HH.", page_icon="📊", layout="wide")

# --- Paleta de colores definida (consistente para todo el dashboard) ---
#    * Género: F = magenta corporativo, M = azul corporativo
COLOR_F = "#D81B60"      # Mujeres
COLOR_M = "#1E88E5"      # Hombres
COLOR_ACCENT = "#F39C12" # Acentos / tendencia
COLOR_NEUTRAL = "#455A64" # Neutro
COLOR_SEQUENTIAL = "blues"  # Esquema secuencial para valores numéricos (Altair/Vega)

# --- Carga y preparación de datos (soporte a todos los puntos) ---
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Limpiezas mínimas
    df["gender"] = df["gender"].astype(str).str.strip()
    for c in ["birth_date", "hiring_date", "last_performance_date"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce", dayfirst=True)
    for c in ["age","salary","performance_score","average_work_hours","satisfaction_level","absences"]:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

DATA_PATH = "Employee_data.csv"
df = load_data(DATA_PATH)

# Validación de columnas requeridas
required = [
    "name_employee","birth_date","age","gender","marital_status","hiring_date",
    "position","salary","performance_score","last_performance_date",
    "average_work_hours","satisfaction_level","absences"
]
missing = [c for c in required if c not in df.columns]
if missing:
    st.error(f"Faltan columnas requeridas en el CSV: {missing}")
    st.stop()

# (1) CÓDIGO PARA TÍTULO Y BREVE DESCRIPCIÓN DE LA APLICACIÓN WEB
# ==============================================================
st.title("📊 Dashboard Ejecutivo — Talento y Desempeño")
st.markdown(
    "Explora **desempeño, horas trabajadas, edad y salarios** para apoyar decisiones. "
    "Se emplean **colores consistentes** (p. ej., **Mujeres** y **Hombres**) para una lectura rápida."
)

# (2) CÓDIGO PARA DESPLEGAR EL LOGOTIPO DE LA EMPRESA
# ==============================================================
with st.sidebar:
    st.header("Socialize your knowledge")
    logo_path = Path("logo.png")  
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True, caption="SAIKAVI") 
    else:
        st.info("Sube tu archivo de logo como **logo.png** para mostrarlo aquí.")

# (3) CÓDIGO PARA CONTROL DE SELECCIÓN DE GÉNERO DEL EMPLEADO
# ==============================================================
st.sidebar.header("Filtros")
genders = ["Todos"] + sorted(df["gender"].dropna().unique().tolist())
gender_sel = st.sidebar.selectbox("Género del empleado", options=genders, index=0)

# (4) CÓDIGO PARA CONTROL DE RANGO DE PUNTAJE DE DESEMPEÑO
# ==============================================================
perf_min = int(np.nanmin(df["performance_score"]))
perf_max = int(np.nanmax(df["performance_score"]))
perf_range = st.sidebar.slider(
    "Rango del puntaje de desempeño (1–5)",
    min_value=perf_min, max_value=perf_max,
    value=(perf_min, perf_max), step=1
)

# (5) CÓDIGO PARA CONTROL DE SELECCIÓN DE ESTADO CIVIL
# ==============================================================
maritals = ["Todos"] + sorted(df["marital_status"].dropna().unique().tolist())
marital_sel = st.sidebar.selectbox("Estado civil", options=maritals, index=0)

# --- Aplicación de filtros globales (alimenta todos los gráficos) ---
flt = df.copy()
if gender_sel != "Todos":
    flt = flt[flt["gender"] == gender_sel]
flt = flt[(flt["performance_score"] >= perf_range[0]) & (flt["performance_score"] <= perf_range[1])]
if marital_sel != "Todos":
    flt = flt[flt["marital_status"] == marital_sel]

st.caption(f"Registros visibles tras filtros: **{len(flt):,}**")

# Layout en dos filas de gráficos
col1, col2 = st.columns(2, gap="large")
col3, col4 = st.columns(2, gap="large")

# (6) GRÁFICO: DISTRIBUCIÓN DE PUNTAJES DE DESEMPEÑO (HISTOGRAMA)
# ==============================================================
with col1:
    st.subheader("Distribución de puntajes de desempeño") 
    perf_data = flt.dropna(subset=["performance_score"]).copy()
    # Para coloreo: variable binned (1–5) con esquema secuencial
    chart_perf = (
        alt.Chart(perf_data)
        .mark_bar()
        .encode(
            x=alt.X("performance_score:Q", bin=alt.Bin(step=1), title="Puntaje de desempeño"),
            y=alt.Y("count():Q", title="Número de empleados"),
            color=alt.Color(
                "performance_score:Q",
                bin=alt.Bin(step=1),
                scale=alt.Scale(scheme=COLOR_SEQUENTIAL),
                title="Puntaje"
            ),
            tooltip=[alt.Tooltip("count():Q", title="Empleados")]
        )
        .properties(height=320)
    )
    st.altair_chart(chart_perf, use_container_width=True)

# (7) GRÁFICO: PROMEDIO DE HORAS TRABAJADAS POR GÉNERO (BARRAS)
# ==============================================================
with col2:
    st.subheader("Promedio de horas trabajadas por género")
    avg_hours_gender = (
        flt.dropna(subset=["gender","average_work_hours"])
           .groupby("gender", as_index=False)["average_work_hours"].mean()
           .rename(columns={"average_work_hours":"avg_hours"})
    )
    # Asegurar dominio para mapear colores aunque falte una categoría
    gender_domain = ["F", "M"]
    gender_range = [COLOR_F, COLOR_M]
    bars_hours = (
        alt.Chart(avg_hours_gender)
        .mark_bar()
        .encode(
            x=alt.X("gender:N", title="Género"),
            y=alt.Y("avg_hours:Q", title="Horas promedio/mes"),
            color=alt.Color("gender:N", title="Género", scale=alt.Scale(domain=gender_domain, range=gender_range)),
            tooltip=["gender", alt.Tooltip("avg_hours:Q", format=".1f")]
        )
        .properties(height=320)
    )
    st.altair_chart(bars_hours, use_container_width=True)

# (8) GRÁFICO: EDAD DE EMPLEADOS VS SALARIO (DISPERSIÓN)
# ==============================================================
with col3:
    st.subheader("Relación entre edad y salario")
    base_age_salary = flt.dropna(subset=["age","salary","gender"]).copy()
    scatter_age_salary = (
        alt.Chart(base_age_salary)
        .mark_circle(opacity=0.7)
        .encode(
            x=alt.X("age:Q", title="Edad"),
            y=alt.Y("salary:Q", title="Salario"),
            color=alt.Color(
                "gender:N", title="Género",
                scale=alt.Scale(domain=["F","M"], range=[COLOR_F, COLOR_M])
            ),
            tooltip=["name_employee","position","gender","age","salary"]
        )
        .properties(height=340)
    )
    st.altair_chart(scatter_age_salary, use_container_width=True)

# (9) GRÁFICO: HORAS PROMEDIO TRABAJADAS VS PUNTAJE DE DESEMPEÑO
# ==============================================================
with col4:
    st.subheader("Horas trabajadas vs puntaje de desempeño")
    base_hp = flt.dropna(subset=["average_work_hours","performance_score"]).copy()
    base_hp["perf_bin"] = pd.cut(base_hp["performance_score"], bins=[0.5,1.5,2.5,3.5,4.5,5.5],
                                 labels=["1","2","3","4","5"])
    scat_hp = (
        alt.Chart(base_hp)
        .mark_circle(opacity=0.7)
        .encode(
            x=alt.X("average_work_hours:Q", title="Promedio de horas/mes"),
            y=alt.Y("performance_score:Q", title="Puntaje de desempeño"),
            color=alt.Color(
                "perf_bin:N", title="Rango desempeño",
                scale=alt.Scale(domain=["1","2","3","4","5"],
                                range=["#90CAF9","#64B5F6","#42A5F5","#1E88E5","#1565C0"])  # azul más intenso a mayor desempeño
            ),
            tooltip=["name_employee","position",
                     alt.Tooltip("average_work_hours:Q", title="Horas", format=".1f"),
                     "performance_score"]
        )
        .properties(height=340)
    )
    reg_hp = (
        alt.Chart(base_hp)
        .transform_regression("average_work_hours", "performance_score")
        .mark_line(stroke=COLOR_ACCENT, strokeWidth=3)
        .encode(x="average_work_hours:Q", y="performance_score:Q")
    )
    st.altair_chart(scat_hp + reg_hp, use_container_width=True)

# (10) CÓDIGO PARA DESPLEGAR UNA CONCLUSIÓN
# ==============================================================
st.subheader("Conclusión")
high_perf = (flt["performance_score"] >= 4).mean() * 100 if len(flt) else 0
avg_hours = flt["average_work_hours"].mean()
avg_salary = flt["salary"].mean()
st.markdown(
    f"""
- **Alto desempeño (4–5):** {high_perf:0.1f}% del personal visible tras filtros.  
- **Horas promedio:** {avg_hours:0.1f} h/mes — revisar equipos con cargas superiores a la media si se observan focos ámbar.  
- **Salario promedio:** ${avg_salary:,.0f} — observar brechas en el gráfico edad–salario (**colores por género**).

> **Recomendación:** priorizar **planes de mejora** donde el puntaje de desempeño sea bajo y la carga horaria alta; y reforzar **retención** en los grupos con alto desempeño y alta satisfacción.

- D.R Vanessa Benavides García"""
)