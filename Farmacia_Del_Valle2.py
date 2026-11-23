from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(
    page_title="Farmacias del Valle | Executive Business Intelligence",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilos CSS ejecutivos de alto nivel visual
st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.5rem;
            padding-bottom: 2.5rem;
            max-width: 96%;
        }
        .exec-header {
            background: linear-gradient(135deg, #0F294A 0%, #1B4372 100%);
            color: #FFFFFF;
            padding: 24px 28px;
            border-radius: 12px;
            border-left: 6px solid #0D9488;
            margin-bottom: 18px;
            box-shadow: 0 4px 14px rgba(15, 41, 74, 0.12);
        }
        .exec-kicker {
            font-size: 0.78rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: #99F6E4;
            font-weight: 700;
            margin-bottom: 6px;
        }
        .exec-title {
            font-size: 1.75rem;
            font-weight: 700;
            line-height: 1.2;
            margin: 0 0 8px 0;
            color: #FFFFFF;
        }
        .exec-subtitle {
            font-size: 0.96rem;
            color: #E2E8F0;
            margin: 0;
            line-height: 1.45;
        }
        div[data-testid="stMetric"] {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-top: 4px solid #1D63B8;
            padding: 16px 18px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        }
        div[data-testid="stMetric"] label {
            color: #475569 !important;
            font-weight: 600 !important;
        }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {
            color: #0F294A !important;
            font-weight: 700 !important;
        }
        .chart-card {
            background-color: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 10px;
            padding: 14px 16px 6px 16px;
            box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
            margin-bottom: 14px;
        }
        .insight-box {
            background-color: #F0FDFA;
            border: 1px solid #99F6E4;
            border-left: 5px solid #0D9488;
            padding: 14px 18px;
            border-radius: 8px;
            color: #134E4A;
            margin-top: 10px;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            background-color: #F1F5F9;
            border-radius: 8px 8px 0 0;
            padding: 10px 18px;
            font-weight: 600;
            color: #334155;
        }
        .stTabs [aria-selected="true"] {
            background-color: #0F294A !important;
            color: #FFFFFF !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

PALETA_EJECUTIVA = [
    "#0F294A",
    "#1D63B8",
    "#0D9488",
    "#4F46E5",
    "#D97706",
    "#64748B",
]


def localizar_csv() -> Path | None:
    base_dir = Path(__file__).resolve().parent
    candidatos = [
        base_dir / "Farmacias_Valle_Demanda.csv",
        base_dir / "Farmacias_Valle_Demanda_1200 (1).csv",
        base_dir / "farmacias_valle_demanda.csv",
    ]
    for ruta in candidatos:
        if ruta.exists():
            return ruta
    return None


@st.cache_data
def cargar_datos(ruta_csv: str) -> pd.DataFrame:
    df = pd.read_csv(ruta_csv)

    # Normalizar fecha del mes (soporta YYYY-MM o YYYY/MM)
    mes_limpio = df["Mes"].astype(str).str.strip().str.replace("/", "-", regex=False)
    df["Fecha_Mes"] = pd.to_datetime(mes_limpio + "-01", errors="coerce")
    df = df.dropna(subset=["Fecha_Mes"]).copy()

    # Asegurar tipos numéricos limpios para evitar TypeError
    for col in ["Unidades_Vendidas", "Precio_Promedio", "Ingreso_Mensual", "Stock_Disponible", "Promocion"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "Ingreso_Mensual" not in df.columns or df["Ingreso_Mensual"].isna().all():
        df["Ingreso_Mensual"] = df["Unidades_Vendidas"] * df["Precio_Promedio"]

    df["Unidades_Vendidas"] = df["Unidades_Vendidas"].fillna(0)
    df["Stock_Disponible"] = df["Stock_Disponible"].fillna(0)
    df["Ingreso_Mensual"] = df["Ingreso_Mensual"].fillna(0.0)
    df["Promocion"] = df["Promocion"].fillna(0).astype(int)

    df["Anio"] = df["Fecha_Mes"].dt.year.astype(int)
    df["Mes_Corto"] = df["Fecha_Mes"].dt.strftime("%b")
    df["Mes_Etiqueta"] = df["Fecha_Mes"].dt.strftime("%Y-%m")
    df["Cobertura_Meses"] = df["Stock_Disponible"] / df["Unidades_Vendidas"].replace(0, pd.NA)
    df["Estado_Promocion"] = df["Promocion"].map({
        0: "Sin promocion",
        1: "Con promocion",
    }).fillna("Sin promocion")

    return df


ruta_archivo = localizar_csv()
if ruta_archivo is None:
    st.error(
        "No se encontro el archivo CSV en el repositorio. Verifica que "
        "'Farmacias_Valle_Demanda.csv' este subido en la misma carpeta que Farmacia_Del_Valle2.py."
    )
    st.stop()

df = cargar_datos(str(ruta_archivo))

# --- PANEL LATERAL DE FILTROS INTERACTIVOS ---
st.sidebar.markdown("### Panel de control y filtros")
st.sidebar.caption(
    "Ajusta el periodo y los segmentos para recalcular KPIs y graficas."
)

anios_disponibles = sorted(df["Anio"].unique())
anio_sel = st.sidebar.selectbox(
    "Ano fiscal",
    options=anios_disponibles,
    index=len(anios_disponibles) - 1,
)

categorias_disponibles = sorted(df["Categoria"].dropna().unique())
categorias_sel = st.sidebar.multiselect(
    "Categorias de productos",
    options=categorias_disponibles,
    default=categorias_disponibles,
)

temporadas_disponibles = sorted(df["Temporada"].dropna().unique())
temporadas_sel = st.sidebar.multiselect(
    "Temporadas",
    options=temporadas_disponibles,
    default=temporadas_disponibles,
)

promo_sel = st.sidebar.radio(
    "Estado promocional",
    options=["Todos", "Con promocion", "Sin promocion"],
    index=0,
)

if not categorias_sel or not temporadas_sel:
    st.warning(
        "Selecciona al menos una categoria y una temporada en la barra lateral."
    )
    st.stop()


def aplicar_filtros(base_df: pd.DataFrame, anio_objetivo: int) -> pd.DataFrame:
    filtrado = base_df[
        (base_df["Anio"] == anio_objetivo)
        & (base_df["Categoria"].isin(categorias_sel))
        & (base_df["Temporada"].isin(temporadas_sel))
    ]
    if promo_sel != "Todos":
        filtrado = filtrado[filtrado["Estado_Promocion"] == promo_sel]
    return filtrado


df_actual = aplicar_filtros(df, anio_sel)
df_anterior = aplicar_filtros(df, anio_sel - 1)

if df_actual.empty:
    st.info(
        "No hay registros para la combinacion de filtros seleccionada en el ano "
        f"{anio_sel}."
    )
    st.stop()

# --- ENCABEZADO NARRATIVO EJECUTIVO ---
totales_cat = df_actual.groupby("Categoria")["Ingreso_Mensual"].sum()
cat_lider = totales_cat.idxmax()
ingreso_total_cat_lider = float(totales_cat.max())
ingreso_total_periodo = float(df_actual["Ingreso_Mensual"].sum())
pct_lider = (
    (ingreso_total_cat_lider / ingreso_total_periodo * 100)
    if ingreso_total_periodo > 0
    else 0.0
)

st.markdown(
    f"""
    <div class="exec-header">
        <div class="exec-kicker">Farmacias del Valle | Inteligencia Comercial y de Abasto ({anio_sel})</div>
        <h1 class="exec-title">Crecimiento Sostenido Liderado por {cat_lider} ({pct_lider:.1f}% de Participacion)</h1>
        <p class="exec-subtitle">
            Tablero de monitoreo para Direccion Comercial y Operaciones: evalua ingresos, rotacion de unidades,
            efecto estacional y cobertura de inventario para respaldar compras y campanas promocionales.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --- 4 KPIs EJECUTIVOS CON CONTEXTO VS. PERIODO ANTERIOR ---
ing_act = float(df_actual["Ingreso_Mensual"].sum())
ing_ant = float(df_anterior["Ingreso_Mensual"].sum()) if not df_anterior.empty else 0.0
var_ing = ((ing_act - ing_ant) / ing_ant * 100) if ing_ant > 0 else None

uni_act = int(df_actual["Unidades_Vendidas"].sum())
uni_ant = int(df_anterior["Unidades_Vendidas"].sum()) if not df_anterior.empty else 0
var_uni = ((uni_act - uni_ant) / uni_ant * 100) if uni_ant > 0 else None

prom_ing_act = float(df_actual["Ingreso_Mensual"].mean())
prom_ing_ant = float(df_anterior["Ingreso_Mensual"].mean()) if not df_anterior.empty else 0.0
var_prom_ing = (
    ((prom_ing_act - prom_ing_ant) / prom_ing_ant * 100)
    if prom_ing_ant > 0
    else None
)

cob_act_series = pd.to_numeric(df_actual["Cobertura_Meses"], errors="coerce").dropna()
cob_act = float(cob_act_series.mean()) if not cob_act_series.empty else None

cob_ant_series = (
    pd.to_numeric(df_anterior["Cobertura_Meses"], errors="coerce").dropna()
    if not df_anterior.empty
    else pd.Series(dtype="float64")
)
cob_ant = float(cob_ant_series.mean()) if not cob_ant_series.empty else None
var_cob = (cob_act - cob_ant) if (cob_act is not None and cob_ant is not None) else None

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    label=f"Ingreso acumulado ({anio_sel})",
    value=f"${ing_act:,.2f}",
    delta=(
        f"{var_ing:+.2f}% vs. {anio_sel - 1}"
        if var_ing is not None
        else "Ano base sin historial previo"
    ),
)
k2.metric(
    label=f"Unidades vendidas ({anio_sel})",
    value=f"{uni_act:,}",
    delta=(
        f"{var_uni:+.2f}% vs. {anio_sel - 1}"
        if var_uni is not None
        else "Ano base sin historial previo"
    ),
)
k3.metric(
    label="Ingreso promedio por registro",
    value=f"${prom_ing_act:,.2f}",
    delta=(
        f"{var_prom_ing:+.2f}% vs. {anio_sel - 1}"
        if var_prom_ing is not None
        else "Ano base sin historial previo"
    ),
)
k4.metric(
    label="Cobertura promedio de stock",
    value=f"{cob_act:.2f} meses" if cob_act is not None else "N/A",
    delta=(
        f"{var_cob:+.2f} meses vs. {anio_sel - 1}"
        if var_cob is not None
        else "Ano base sin historial previo"
    ),
)

st.write("")

# --- PESTAÑAS PARA UNA NAVEGACION LIMPIA Y DE ALTO IMPACTO ---
tab1, tab2, tab3 = st.tabs([
    "Panorama Ejecutivo",
    "Estacionalidad y Promociones",
    "Detalle de Inventario y Datos",
])

with tab1:
    col_izq, col_der = st.columns([1.35, 1])

    with col_izq:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("#### Tendencia mensual de ingresos y promedio del periodo")
        tendencia = (
            df_actual.groupby("Mes_Etiqueta", as_index=False)["Ingreso_Mensual"]
            .sum()
            .sort_values("Mes_Etiqueta")
        )
        promedio_mensual = float(tendencia["Ingreso_Mensual"].mean())

        fig_tend = go.Figure()
        fig_tend.add_trace(
            go.Scatter(
                x=tendencia["Mes_Etiqueta"],
                y=tendencia["Ingreso_Mensual"],
                mode="lines+markers",
                name="Ingreso mensual",
                line=dict(color="#0F294A", width=3),
                marker=dict(size=7, color="#0D9488"),
                hovertemplate="<b>Mes:</b> %{x}<br><b>Ingreso:</b> $%{y:,.2f}<extra></extra>",
            )
        )
        fig_tend.add_hline(
            y=promedio_mensual,
            line_dash="dash",
            line_color="#D97706",
            annotation_text=f"Promedio mensual: ${promedio_mensual:,.0f}",
            annotation_position="top left",
        )
        fig_tend.update_layout(
            template="plotly_white",
            height=360,
            margin=dict(t=24, b=24, l=10, r=10),
            xaxis_title="Mes",
            yaxis_title="Ingreso mensual ($)",
            legend=dict(orientation="h", y=1.12, x=0),
        )
        st.plotly_chart(fig_tend, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with col_der:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("#### Distribucion de ingresos por categoria")
        dist_cat = (
            df_actual.groupby("Categoria", as_index=False)["Ingreso_Mensual"]
            .sum()
            .sort_values("Ingreso_Mensual", ascending=False)
        )
        fig_donut = px.pie(
            dist_cat,
            names="Categoria",
            values="Ingreso_Mensual",
            hole=0.52,
            color_discrete_sequence=PALETA_EJECUTIVA,
            template="plotly_white",
        )
        fig_donut.update_traces(
            textposition="inside",
            textinfo="percent+label",
            hovertemplate="<b>%{label}</b><br>Ingreso: $%{value:,.2f}<br>Participacion: %{percent}<extra></extra>",
        )
        fig_donut.update_layout(
            height=360,
            margin=dict(t=24, b=24, l=10, r=10),
            showlegend=False,
        )
        st.plotly_chart(fig_donut, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("#### Comparacion: Top productos por ingreso acumulado")
    top_prod = (
        df_actual.groupby("Producto_Nombre", as_index=False)["Ingreso_Mensual"]
        .sum()
        .sort_values("Ingreso_Mensual", ascending=True)
        .tail(10)
    )
    fig_bar = px.bar(
        top_prod,
        x="Ingreso_Mensual",
        y="Producto_Nombre",
        orientation="h",
        text=top_prod["Ingreso_Mensual"].apply(lambda v: f"${v:,.0f}"),
        color="Ingreso_Mensual",
        color_continuous_scale=["#93C5FD", "#1D63B8", "#0F294A"],
        template="plotly_white",
    )
    fig_bar.update_traces(
        textposition="outside",
        hovertemplate="<b>%{y}</b><br>Ingreso: $%{x:,.2f}<extra></extra>",
    )
    fig_bar.update_layout(
        height=390,
        margin=dict(t=20, b=20, l=10, r=70),
        xaxis_title="Ingreso acumulado ($)",
        yaxis_title="",
        coloraxis_showscale=False,
    )
    st.plotly_chart(fig_bar, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with tab2:
    c_a, c_b = st.columns(2)

    with c_a:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("#### Unidades promedio por temporada y promocion")
        promo_temp = (
            df[
                (df["Anio"] == anio_sel)
                & (df["Categoria"].isin(categorias_sel))
                & (df["Temporada"].isin(temporadas_sel))
            ]
            .groupby(["Temporada", "Estado_Promocion"], as_index=False)[
                "Unidades_Vendidas"
            ]
            .mean()
        )
        fig_promo = px.bar(
            promo_temp,
            x="Temporada",
            y="Unidades_Vendidas",
            color="Estado_Promocion",
            barmode="group",
            text=promo_temp["Unidades_Vendidas"].apply(lambda v: f"{v:,.0f}"),
            color_discrete_map={
                "Sin promocion": "#64748B",
                "Con promocion": "#0D9488",
            },
            template="plotly_white",
        )
        fig_promo.update_traces(textposition="outside")
        fig_promo.update_layout(
            height=370,
            margin=dict(t=24, b=24, l=10, r=10),
            xaxis_title="Temporada",
            yaxis_title="Unidades promedio por registro",
            legend_title="Estrategia",
        )
        st.plotly_chart(fig_promo, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with c_b:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown("#### Mapa de calor: Ingresos por categoria y mes")
        heatmap_df = df_actual.pivot_table(
            index="Categoria",
            columns="Mes_Corto",
            values="Ingreso_Mensual",
            aggfunc="sum",
            fill_value=0,
        )
        orden_meses = [
            m
            for m in [
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ]
            if m in heatmap_df.columns
        ]
        heatmap_df = heatmap_df[orden_meses]

        fig_heat = px.imshow(
            heatmap_df,
            text_auto=",.0f",
            aspect="auto",
            color_continuous_scale="Teal",
            template="plotly_white",
        )
        fig_heat.update_layout(
            height=370,
            margin=dict(t=24, b=24, l=10, r=10),
            xaxis_title="Mes",
            yaxis_title="Categoria",
            coloraxis_colorbar=dict(title="Ingreso ($)"),
        )
        st.plotly_chart(fig_heat, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown("#### Detalle de demanda e inventario filtrado")

    resumen_tabla = df_actual[[
        "Mes_Etiqueta",
        "Producto_ID",
        "Producto_Nombre",
        "Categoria",
        "Temporada",
        "Estado_Promocion",
        "Unidades_Vendidas",
        "Precio_Promedio",
        "Ingreso_Mensual",
        "Stock_Disponible",
        "Cobertura_Meses",
    ]].sort_values(["Mes_Etiqueta", "Ingreso_Mensual"], ascending=[True, False])

    st.dataframe(
        resumen_tabla,
        use_container_width=True,
        height=380,
        column_config={
            "Mes_Etiqueta": "Mes",
            "Producto_ID": "ID",
            "Producto_Nombre": "Producto",
            "Categoria": "Categoria",
            "Temporada": "Temporada",
            "Estado_Promocion": "Promocion",
            "Unidades_Vendidas": st.column_config.NumberColumn(
                "Unidades", format="%d"
            ),
            "Precio_Promedio": st.column_config.NumberColumn(
                "Precio prom.", format="$%.2f"
            ),
            "Ingreso_Mensual": st.column_config.NumberColumn(
                "Ingreso mensual", format="$%.2f"
            ),
            "Stock_Disponible": st.column_config.NumberColumn(
                "Stock", format="%d"
            ),
            "Cobertura_Meses": st.column_config.NumberColumn(
                "Cobertura (meses)", format="%.2f"
            ),
        },
        hide_index=True,
    )

    csv_export = resumen_tabla.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label="Descargar seleccion filtrada (CSV)",
        data=csv_export,
        file_name=f"farmacias_valle_{anio_sel}_filtrado.csv",
        mime="text/csv",
    )
    st.markdown("</div>", unsafe_allow_html=True)

st.markdown(
    """
    <div class="insight-box">
        <strong>Sintesis para toma de decisiones:</strong> Contrastar la evolucion mensual de ingresos frente a la media del
        periodo y revisar el mapa de calor por categoria permite anticipar compras de reposicion antes de los picos de
        demanda, evitando quiebres de stock o exceso de inventario inmovilizado.
    </div>
    """,
    unsafe_allow_html=True,
)