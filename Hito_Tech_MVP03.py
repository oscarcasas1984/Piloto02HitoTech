

# ==============================================================
# Hito_Tech_MVP03.py
# Portafolio Tecnológico – MVP03
# Metodología 3×3:
#   - VALOR (VEOB)
#   - EJECUTABILIDAD / INDUSTRIALIZACIÓN
#   - PREPARACIÓN ORGANIZACIONAL
# Excel = fuente de verdad de los scores
# Python/Streamlit = lectura, validación, visualización y análisis
# ==============================================================

from __future__ import annotations

import math
from datetime import datetime
from typing import List, Tuple, Optional

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# --------------------------------------------------------------
# Configuración general
# --------------------------------------------------------------
st.set_page_config(
    page_title="HITO – Portafolio Tecnológico (MVP03)",
    page_icon="🧭",
    layout="wide",
)

# Umbrales (ajustables)
TH_VALOR = 3.5
TH_EJECUT = 3.5
TH_PREP = 3.5
TH_TRL = 6
TH_AVANCE = 70

# --------------------------------------------------------------
# Contrato de columnas
# --------------------------------------------------------------
INTOCABLES = [
    "ID_Tecnologia",
    "Nombre_Tecnologia",
    "Familia_Tecnologica",
    "Tipo_Tecnologia",
    "Descripcion_Corta",
    "Responsable",
    "TRL",
    "Estado",
    "Avance_Plan_%",
    "Fecha_Ultima_Actualizacion",
    "Comentarios_Generales",
    "Score_TRL",
]

SUBCRITERIOS_3X3 = [
    # VALOR
    "VALOR_Impacto_Economico",
    "VALOR_Problema_Critico",
    "VALOR_Ventaja_Estrategica",
    # EJECUTABILIDAD
    "EJEC_Robustez_Operativa",
    "EJEC_Capacidad_Instalada",
    "EJEC_Escalabilidad",
    # PREPARACIÓN
    "PREP_Demanda_Negocio",
    "PREP_Gobierno_Absorcion",
    "PREP_Timing_Estrategico",
]

SCORES_AGREGADOS = [
    "Score_VALOR",
    "Score_EJECUTABILIDAD",
    "Score_PREPARACION",
]

# --------------------------------------------------------------
# Utilidades
# --------------------------------------------------------------

def to_num(s: pd.Series, fill: float = 0.0, clip: Optional[Tuple[float, float]] = None) -> pd.Series:
    out = pd.to_numeric(s, errors="coerce").fillna(fill)
    if clip is not None:
        lo, hi = clip
        out = out.clip(lo, hi)
    return out


def safe_str(x) -> str:
    if x is None:
        return ""
    if isinstance(x, float) and math.isnan(x):
        return ""
    return str(x)


def semaforo(score: float) -> str:
    try:
        s = float(score)
    except Exception:
        s = 0.0
    if s >= 4:
        return "🟩"
    if s >= 3:
        return "🟨"
    if s > 0:
        return "🟥"
    return "⚪"


def fmt(x) -> str:
    try:
        return f"{float(x):.2f}"
    except Exception:
        return "0.00"

# --------------------------------------------------------------
# Carga y validación de datos
# --------------------------------------------------------------

def load_excel(file) -> pd.DataFrame:
    try:
        return pd.read_excel(file, sheet_name="Portafolio")
    except Exception:
        return pd.read_excel(file)


def validar_contrato(df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    miss_int = [c for c in INTOCABLES if c not in df.columns]
    miss_new = [c for c in (SUBCRITERIOS_3X3 + SCORES_AGREGADOS) if c not in df.columns]
    return miss_int, miss_new


def limpiar_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Garantizar columnas intocables
    for c in INTOCABLES:
        if c not in df.columns:
            df[c] = ""

    # Tipos básicos
    df["TRL"] = to_num(df["TRL"], 0, (0, 9))
    df["Avance_Plan_%"] = to_num(df["Avance_Plan_%"], 0, (0, 100))
    df["Score_TRL"] = to_num(df["Score_TRL"], 0, (0, 5))

    if "Fecha_Ultima_Actualizacion" in df.columns:
        df["Fecha_Ultima_Actualizacion"] = pd.to_datetime(df["Fecha_Ultima_Actualizacion"], errors="coerce")

    # Subcriterios y scores
    for c in SUBCRITERIOS_3X3 + SCORES_AGREGADOS:
        if c in df.columns:
            df[c] = to_num(df[c], 0, (0, 5))
        else:
            df[c] = 0

    # Fallback de scores agregados
    if df["Score_VALOR"].sum() == 0:
        df["Score_VALOR"] = df[[
            "VALOR_Impacto_Economico",
            "VALOR_Problema_Critico",
            "VALOR_Ventaja_Estrategica",
        ]].mean(axis=1)

    if df["Score_EJECUTABILIDAD"].sum() == 0:
        df["Score_EJECUTABILIDAD"] = df[[
            "EJEC_Robustez_Operativa",
            "EJEC_Capacidad_Instalada",
            "EJEC_Escalabilidad",
        ]].mean(axis=1)

    if df["Score_PREPARACION"].sum() == 0:
        df["Score_PREPARACION"] = df[[
            "PREP_Demanda_Negocio",
            "PREP_Gobierno_Absorcion",
            "PREP_Timing_Estrategico",
        ]].mean(axis=1)

    # Alias UX
    df["Score_Valor"] = df["Score_VALOR"]

    # Semáforos
    df["S_VALOR"] = df["Score_VALOR"].apply(semaforo)
    df["S_EJECUT"] = df["Score_EJECUTABILIDAD"].apply(semaforo)
    df["S_PREP"] = df["Score_PREPARACION"].apply(semaforo)

    # Limpieza strings
    for c in [
        "ID_Tecnologia",
        "Nombre_Tecnologia",
        "Familia_Tecnologica",
        "Tipo_Tecnologia",
        "Descripcion_Corta",
        "Responsable",
        "Estado",
        "Comentarios_Generales",
    ]:
        df[c] = df[c].apply(safe_str)

    return df

# --------------------------------------------------------------
# Filtros
# --------------------------------------------------------------

def filtros(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.header("Filtros")

    fam = sorted([x for x in df["Familia_Tecnologica"].unique() if x])
    est = sorted([x for x in df["Estado"].unique() if x])

    fam_sel = st.sidebar.multiselect("Familia tecnológica", fam, default=fam)
    est_sel = st.sidebar.multiselect("Estado", est, default=est)

    trl_min, trl_max = st.sidebar.slider("TRL", 0, 9, (0, 9))
    vmin = st.sidebar.slider("Score VALOR mínimo", 0.0, 5.0, 0.0, 0.5)

    q = st.sidebar.text_input("Buscar", "").lower().strip()

    out = df.copy()
    if fam_sel:
        out = out[out["Familia_Tecnologica"].isin(fam_sel)]
    if est_sel:
        out = out[out["Estado"].isin(est_sel)]

    out = out[(out["TRL"] >= trl_min) & (out["TRL"] <= trl_max)]
    out = out[out["Score_VALOR"] >= vmin]

    if q:
        out = out[
            out["ID_Tecnologia"].str.lower().str.contains(q)
            | out["Nombre_Tecnologia"].str.lower().str.contains(q)
            | out["Descripcion_Corta"].str.lower().str.contains(q)
        ]

    return out

# --------------------------------------------------------------
# Visualizaciones
# --------------------------------------------------------------

def kpis(df: pd.DataFrame):
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Tecnologías", len(df))
    with c2:
        st.metric("Valor promedio", fmt(df["Score_VALOR"].mean() if len(df) else 0))
    with c3:
        st.metric("Ejecut promedio", fmt(df["Score_EJECUTABILIDAD"].mean() if len(df) else 0))
    with c4:
        st.metric("Prep promedio", fmt(df["Score_PREPARACION"].mean() if len(df) else 0))


def mapa(df: pd.DataFrame, key: str):
    fig = px.scatter(
        df,
        x="TRL",
        y="Score_VALOR",
        color="Familia_Tecnologica",
        size="Avance_Plan_%",
        hover_data=["ID_Tecnologia", "Nombre_Tecnologia", "Estado"],
        size_max=30,
    )
    fig.add_hline(y=TH_VALOR, line_dash="dash")
    fig.add_vline(x=TH_TRL, line_dash="dash")
    fig.update_layout(height=520, yaxis_title="Score VALOR (0–5)")
    st.plotly_chart(fig, use_container_width=True, key=key)


def barras_3(row, key):
    d = pd.DataFrame({
        "Dimensión": ["Valor", "Ejecutabilidad", "Preparación"],
        "Score": [row["Score_VALOR"], row["Score_EJECUTABILIDAD"], row["Score_PREPARACION"]],
    })
    fig = px.bar(d, x="Dimensión", y="Score", range_y=[0, 5])
    fig.update_layout(height=320)
    st.plotly_chart(fig, use_container_width=True, key=key)


def barras_9(row, key):
    d = pd.DataFrame({
        "Subcriterio": SUBCRITERIOS_3X3,
        "Score": [row[c] for c in SUBCRITERIOS_3X3],
    })
    fig = px.bar(d, x="Subcriterio", y="Score", range_y=[0, 5])
    fig.update_layout(height=380)
    st.plotly_chart(fig, use_container_width=True, key=key)


def tabla(df: pd.DataFrame):
    cols = [
        "ID_Tecnologia",
        "Nombre_Tecnologia",
        "Familia_Tecnologica",
        "Estado",
        "TRL",
        "Avance_Plan_%",
        "Score_VALOR",
        "Score_EJECUTABILIDAD",
        "Score_PREPARACION",
    ]
    st.dataframe(df[cols].sort_values(["Score_VALOR", "TRL"], ascending=False), use_container_width=True)

# --------------------------------------------------------------
# Drilldown
# --------------------------------------------------------------

def drilldown(df: pd.DataFrame):
    st.subheader("Drilldown")
    if len(df) == 0:
        st.info("No hay tecnologías para mostrar.")
        return

    sel = st.selectbox("Tecnología", df["ID_Tecnologia"].tolist())
    r = df[df["ID_Tecnologia"] == sel].iloc[0]

    st.markdown(f"## {r['Nombre_Tecnologia']}")
    st.caption(f"Familia: {r['Familia_Tecnologica']} · Estado: {r['Estado']} · Responsable: {r['Responsable']}")

    c1, c2, c3 = st.columns(3)
    with c1:
        st.metric("VALOR", fmt(r["Score_VALOR"]))
    with c2:
        st.metric("EJECUTABILIDAD", fmt(r["Score_EJECUTABILIDAD"]))
    with c3:
        st.metric("PREPARACIÓN", fmt(r["Score_PREPARACION"]))

    st.write(f"Semáforo → Valor {r['S_VALOR']} · Ejecut {r['S_EJECUT']} · Prep {r['S_PREP']}")

    barras_3(r, key=f"b3_{sel}")
    with st.expander("Detalle 9 subcriterios"):
        barras_9(r, key=f"b9_{sel}")

    st.markdown("### Descripción")
    st.write(r["Descripcion_Corta"])
    st.markdown("### Comentarios")
    st.write(r["Comentarios_Generales"])

# --------------------------------------------------------------
# App principal
# --------------------------------------------------------------

def main():
    st.title("🧭 HITO – Portafolio Tecnológico (MVP03)")
    st.caption("Metodología 3×3 · Excel = fuente de verdad · TRL independiente")

    up = st.file_uploader("Cargar Excel del portafolio", type=["xlsx", "xls"])
    if up is None:
        st.info("Carga el Excel del portafolio para iniciar.")
        return

    df_raw = load_excel(up)
    miss_int, miss_new = validar_contrato(df_raw)

    if miss_int:
        st.error("Faltan columnas intocables: " + ", ".join(miss_int))
        st.stop()

    if miss_new:
        st.warning("Faltan columnas 3×3 (se asumen 0 o se calculan fallback): " + ", ".join(miss_new))

    df = limpiar_df(df_raw)
    df_f = filtros(df)

    t1, t2, t3, t4 = st.tabs(["Resumen", "Mapa", "Tabla", "Drilldown"])

    with t1:
        kpis(df_f)
    with t2:
        mapa(df_f, key="map")
    with t3:
        tabla(df_f)
    with t4:
        drilldown(df_f)


if __name__ == "__main__":
    main()