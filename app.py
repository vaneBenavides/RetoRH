# ============================================
# MÓDULO 11 — Dashboard Ejecutivo de RR.HH.
# ============================================
# Requisitos:
#   pip install streamlit pandas altair numpy
# Ejecución:
#   streamlit run app.py

import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from pathlib import Path

# -------------------------
# [0] Configuración y estilo
# -------------------------
st.set_page_config(
    page_title="Dashboard Ejecutivo RR.HH.",
    page_icon="🏢",
    layout="wide"
)

# Paleta ejecutiva (puedes ajustar a tus colores corporativos)
PRIMARY = "#1F4E79"     # azul institucional
ACCENT  = "#F39C12"     # ámbar para acentos/KPI
NEUTRAL = "#F5F7FA"     # gris muy claro fondo
OK      = "#2ECC71"     # verde
WARN    = "#E67E22"     # naranja
ALERT   = "#E74C3C"     # rojo

# CSS para tarjetas KPI y contenedores
st.markdown(f"""
<style>
/* Fondo general */
.main .block-container {{
  padding-top: 1rem;
  padding-bottom: 2rem;
}}

/* Tarjetas KPI */
.kpi-card {{
  background: white;
  border-radius: 16px;
  padding: 18px 20px;
  border: 1px solid #eaecef;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}}
.kpi-title {{
  color: #6b7280; 
  font-size: 0.8rem; 
  text-transform: uppercase; 
  letter-spacing: .06em;
  margin-bottom: 6px;
}}
.kpi-value {{
  font-size: 1.8rem; 
  font-weight: 800; 
  color: {PRIMARY};
  line-height: 1.1;
}}
.kpi-delta {{
  font-size: .95rem; 
  color: #6b7280;
}}

/* Secciones */
.section-card {{
  background: white;
  border-radius: 16px;
  padding: 18px 20px;
  border: 1px solid #eaecef;
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
}}

/* Titulares */
h1, h2, h3 {{
  color: {PRIMARY};
}}

[data-testid="stSidebar"] {{
  background-color: {NEUTRAL};
  border-right: 1px solid #eaecef;
}}
</style>
""", unsafe_allow_html=True)

# Tema Altair básico
def alt_theme():
    return {
        "config": {
            "view": {"strokeWidth": 0},
            "axis": {"labelColor": "#374151", "titleColor": "#374151"},
            "legend": {"labelColor": "#374151", "titleColor": "#374151"},
            "range": {
                "category": [PRIMARY, ACCENT, OK, WARN, ALERT, "#7E57C2", "#26C6DA"]
            }
        }
    }
alt.themes.register("exec_theme", alt_theme)
alt.themes.enable("exec_theme")

# -------------------------
# [1] Encabezado y logo
# -------------------------
col_title, col_logo = st.columns([0.8, 0.2], vertical_alignment="center")
with col_title:
    st.title("Dashboard Ejecutivo — Talento y Desempeño")
    st.caption("Visión en un vistazo: desempeño, jornada, satisfacción y ausencias para decisiones ágiles.")
with col_logo:
    logo_path = Path("logo.png")
    if logo_path.exists():
        st.image(str(logo_path), use_column_width=True)
    else:
        st.write("")

# -------------------------
# [2] Datos
# -------------------------
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    # Limpieza
    df["gender"] = df["gender"].astype(str).str.strip()
    for col in ["birth_date", "hiring_date", "last_performance_date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce", dayfirst=True)
    num_cols = ["age","salary","performance_score","average_work_hours","satisfaction_level","absences"]
    for c in num_cols:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    return df

DATA_PATH = "Employee_data.csv"
df = load_data(DATA_PATH)

required = [
    "name_employee","birth_date","age","gender","marital_status","hiring_date",
    "position","salary","performance_score","last_performance_date",
    "average_work_hours","satisfaction_level","absences"
]
missing = [c for c in required if c not in df.columns]
if missing:
    st.error(f"Faltan columnas requeridas: {missing}")
    st.stop()

# -------------------------
# [3] Sidebar — Filtros ejecutivos
# -------------------------
st.sidebar.header("🎛️ Filtros")
# Género
genders = ["Todos"] + sorted(df["gender"].dropna().unique().tolist())
gender_sel = st.sidebar.selectbox("Género", genders, index=0)

# Estado civil
maritals = ["Todos"] + sorted(df["marital_status"].dropna().unique().tolist())
marital_sel = st.sidebar.selectbox("Estado civil", maritals, index=0)

# Puntaje desempeño
perf_min = int(np.nanmin(df["performance_score"]))
perf_max = int(np.nanmax(df["performance_score"]))
perf_range = st.sidebar.slider("Puntaje de desempeño", perf_min, perf_max, (perf_min, perf_max), 1)

# Rango salarial (opcional, útil para directivos)
s_min = float(np.nanmin(df["salary"]))
s_max = float(np.nanmax(df["salary"]))
salary_range = st.sidebar.slider("Salario (rango)", float(s_min), float(s_max), (float(s_min), float(s_max)))

# Aplicar filtros
flt = df.copy()
if gender_sel != "Todos":
    flt = flt[flt["gender"] == gender_sel]
if marital_sel != "Todos":
    flt = flt[flt["marital_status"] == marital_sel]
flt = flt[(flt["performance_score"] >= perf_range[0]) & (flt["performance_score"] <= perf_range[1])]
flt = flt[(flt["salary"] >= salary_range[0]) & (flt["salary"] <= salary_range[1])]

st.caption(f"Registros visibles: **{len(flt):,}**")

# -------------------------
# [4] Tarjetas KPI — “Lo esencial primero”
# -------------------------
def kpi(value, title, delta=None):
    st.markdown(f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        {f'<div class="kpi-delta">{delta}</div>' if delta else ''}
    </div>
    """, unsafe_allow_html=True)

col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    headcount = len(flt)
    kpi(f"{headcount:,}", "Headcount")
with col2:
    avg_perf = flt["performance_score"].mean()
    kpi(f"{avg_perf:0.2f}/5", "Puntaje promedio")
with col3:
    avg_hours = flt["average_work_hours"].mean()
    kpi(f"{avg_hours:0.1f} h/mes", "Horas promedio")
with col4:
    avg_salary = flt["salary"].mean()
    kpi(f"${avg_salary:,.0f}", "Salario promedio")
with col5:
    absence_rate = (flt["absences"] > 0).mean() * 100 if len(flt) else 0
    kpi(f"{absence_rate:0.1f}%", "Tasa con ausencias")

# -------------------------
# [5] Tabs Ejecutivas
# -------------------------
tab_overview, tab_performance, tab_workforce, tab_corr, tab_detalles = st.tabs(
    ["📌 Overview", "⭐ Desempeño", "👥 Fuerza Laboral", "🔗 Correlaciones", "📄 Detalles"]
)

# ========== OVERVIEW ==========
with tab_overview:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Resumen ejecutivo")
    c1, c2 = st.columns([1.2, 1], gap="large")

    # Distribución de desempeño (histograma)
    with c1:
        chart_perf = (
            alt.Chart(flt.dropna(subset=["performance_score"]))
            .mark_bar()
            .encode(
                x=alt.X("performance_score:Q", bin=alt.Bin(step=1), title="Puntaje de desempeño"),
                y=alt.Y("count():Q", title="Empleados"),
                tooltip=["count()"]
            )
            .properties(height=320)
        )
        st.altair_chart(chart_perf, use_container_width=True)

    # Composición por estado civil (donut)
    with c2:
        pie_df = (
            flt.dropna(subset=["marital_status"])
               .groupby("marital_status", as_index=False)["name_employee"].count()
               .rename(columns={"name_employee": "count"})
        )
        if len(pie_df):
            pie_df["pct"] = (pie_df["count"] / pie_df["count"].sum() * 100).round(1)
            donut = (
                alt.Chart(pie_df)
                .mark_arc(innerRadius=60)
                .encode(
                    theta="count:Q",
                    color=alt.Color("marital_status:N", legend=alt.Legend(title="Estado civil")),
                    tooltip=["marital_status", "count", "pct"]
                )
                .properties(height=320)
            )
            st.altair_chart(donut, use_container_width=True)
        else:
            st.info("Sin datos suficientes para el gráfico de estado civil.")
    st.markdown('</div>', unsafe_allow_html=True)

# ========== DESEMPEÑO ==========
with tab_performance:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Horas trabajadas y desempeño")

    c1, c2 = st.columns(2, gap="large")

    # Barras: promedio de horas por género
    with c1:
        avg_hours_gender = (
            flt.dropna(subset=["gender","average_work_hours"])
               .groupby("gender", as_index=False)["average_work_hours"].mean()
               .rename(columns={"average_work_hours":"avg_hours"})
        )
        bars = (
            alt.Chart(avg_hours_gender)
            .mark_bar()
            .encode(
                x=alt.X("gender:N", title="Género"),
                y=alt.Y("avg_hours:Q", title="Promedio de horas/mes"),
                tooltip=["gender", alt.Tooltip("avg_hours:Q", format=".1f")]
            ).properties(height=340)
        )
        st.altair_chart(bars, use_container_width=True)

    # Heatmap: desempeño promedio por género/estado civil (rápida lectura)
    with c2:
        perf_pivot = (
            flt.dropna(subset=["gender","marital_status","performance_score"])
               .groupby(["gender","marital_status"], as_index=False)["performance_score"].mean()
        )
        heat = (
            alt.Chart(perf_pivot)
            .mark_rect()
            .encode(
                x=alt.X("gender:N", title="Género"),
                y=alt.Y("marital_status:N", title="Estado civil"),
                color=alt.Color("performance_score:Q", title="Desempeño prom.", scale=alt.Scale(scheme="goldred")),
                tooltip=["gender","marital_status", alt.Tooltip("performance_score:Q", format=".2f")]
            ).properties(height=340)
        )
        st.altair_chart(heat, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ========== FUERZA LABORAL ==========
with tab_workforce:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Estructura de la fuerza laboral")

    c1, c2 = st.columns(2, gap="large")

    # Dispersión: Edad vs. Salario con línea de tendencia
    with c1:
        base = flt.dropna(subset=["age","salary"])
        points = (
            alt.Chart(base)
            .mark_circle(opacity=0.6)
            .encode(
                x=alt.X("age:Q", title="Edad"),
                y=alt.Y("salary:Q", title="Salario"),
                tooltip=["name_employee","position","age","salary"]
            ).properties(height=360)
        )
        trend = (
            alt.Chart(base)
            .transform_regression("age", "salary")
            .mark_line(stroke=ACCENT, strokeWidth=3)
            .encode(x="age:Q", y="salary:Q")
        )
        st.altair_chart(points + trend, use_container_width=True)

    # Barras: Salario promedio por puesto (Top 10)
    with c2:
        sal_pos = (
            flt.dropna(subset=["position","salary"])
               .groupby("position", as_index=False)["salary"].mean()
               .sort_values("salary", ascending=False)
               .head(10)
        )
        bars_pos = (
            alt.Chart(sal_pos)
            .mark_bar()
            .encode(
                y=alt.Y("position:N", sort="-x", title="Puesto"),
                x=alt.X("salary:Q", title="Salario promedio"),
                tooltip=["position", alt.Tooltip("salary:Q", format=",.0f")]
            ).properties(height=360)
        )
        st.altair_chart(bars_pos, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

# ========== CORRELACIONES ==========
with tab_corr:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Relaciones clave para decidir")

    c1, c2 = st.columns(2, gap="large")

    # Horas vs desempeño
    with c1:
        base_hp = flt.dropna(subset=["average_work_hours","performance_score"])
        scat_hp = (
            alt.Chart(base_hp)
            .mark_circle(opacity=0.6)
            .encode(
                x=alt.X("average_work_hours:Q", title="Horas promedio/mes"),
                y=alt.Y("performance_score:Q", title="Puntaje de desempeño"),
                tooltip=["name_employee","position","average_work_hours","performance_score"]
            ).properties(height=360)
        )
        reg_hp = (
            alt.Chart(base_hp)
            .transform_regression("average_work_hours", "performance_score")
            .mark_line(stroke=ACCENT, strokeWidth=3)
            .encode(x="average_work_hours:Q", y="performance_score:Q")
        )
        st.altair_chart(scat_hp + reg_hp, use_container_width=True)

    # Satisfacción vs desempeño (promedios por puesto)
    with c2:
        sat_perf = (
            flt.dropna(subset=["position","satisfaction_level","performance_score"])
               .groupby("position", as_index=False)[["satisfaction_level","performance_score"]].mean()
        )
        corr = (
            alt.Chart(sat_perf)
            .mark_circle(size=100, opacity=0.7)
            .encode(
                x=alt.X("satisfaction_level:Q", title="Satisfacción promedio"),
                y=alt.Y("performance_score:Q", title="Desempeño promedio"),
                tooltip=["position", alt.Tooltip("satisfaction_level:Q", format=".2f"),
                         alt.Tooltip("performance_score:Q", format=".2f")]
            ).properties(height=360)
        )
        st.altair_chart(corr, use_container_width=True)

    # Conclusiones rápidas
    st.markdown("---")
    st.markdown("**Conclusiones automáticas (borrador):**")
    # Ejemplos de heurísticas ejecutivas
    high_perf_share = (flt["performance_score"] >= 4).mean()*100 if len(flt) else 0
    msg_perf = (
        f"- **Alto desempeño:** {high_perf_share:0.1f}% del personal está en 4–5. "
        + ("✅ Nivel saludable." if high_perf_share >= 40 else "⚠️ Oportunidad de mejora.")
    )

    avg_sat = flt["satisfaction_level"].mean()
    msg_sat = (
        f"- **Satisfacción promedio:** {avg_sat:0.2f} "
        + ("✅ En buen rango." if avg_sat and avg_sat >= 3 else "⚠️ Revisar clima laboral.")
    )

    msg_hours = (
        f"- **Horas promedio:** {avg_hours:0.1f} h/mes. "
        + ("⚠️ Vigilar cargas si hay equipos por encima de la media." if avg_hours and avg_hours > np.nanmedian(df['average_work_hours']) else "✅ En línea con la mediana.")
    )
    st.write(msg_perf)
    st.write(msg_sat)
    st.write(msg_hours)
    st.markdown('</div>', unsafe_allow_html=True)

# ========== DETALLES ==========
with tab_detalles:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.subheader("Tabla de detalles (post-filtro)")
    st.dataframe(
        flt[[
            "name_employee","gender","marital_status","position","age","salary",
            "performance_score","average_work_hours","satisfaction_level","absences"
        ]].sort_values(["performance_score","salary"], ascending=[False, False]),
        use_container_width=True,
        height=420
    )
    st.markdown("---")
    st.download_button(
        "Descargar CSV filtrado",
        data=flt.to_csv(index=False).encode("utf-8"),
        file_name="employee_filtered.csv",
        mime="text/csv"
    )
    st.markdown('</div>', unsafe_allow_html=True)

# -------------------------
# [6] Pie de página ejecutivo
# -------------------------
st.caption("© Dirección de Analítica — Dashboard Ejecutivo RR.HH.")