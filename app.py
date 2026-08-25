import streamlit as st
from data_loader import load_data
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Walmart Retail Analysis", page_icon="📊", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@500;700&family=Instrument+Serif:ital@0;1&family=Inter:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; color: #111111; }
    .main { background-color: #FFFFFF; padding-top: 1rem; }

    /* Titre principal en Bricolage Grotesque */
    h1 {
        font-family: 'Bricolage Grotesque', sans-serif;
        color: #111111;
        font-weight: 700;
        font-size: 2.4rem;
        letter-spacing: -0.02em;
    }
    h2, h3 {
        font-family: 'Bricolage Grotesque', sans-serif;
        color: #111111;
        font-weight: 500;
    }

    /* Sous-titre en Instrument Serif, italique */
    .subtitle {
        font-family: 'Instrument Serif', serif;
        font-style: italic;
        color: #555555;
        font-size: 1.3rem;
        margin-bottom: 2.5rem;
    }

    [data-testid="stSidebar"] {
        background-color: #FAFAFA;
        border-right: 1px solid #EAEAEA;
    }
    [data-testid="stSidebar"] h2 {
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #888888;
        font-weight: 500;
    }

    /* KPIs : bordure fine noire, chiffres en mono */
    [data-testid="stMetric"] {
        background-color: #FFFFFF;
        border: 1px solid #111111;
        border-radius: 0px;
        padding: 1.2rem 1.5rem;
    }
    [data-testid="stMetricValue"] {
        font-family: 'IBM Plex Mono', monospace;
        color: #111111;
        font-weight: 500;
        font-size: 1.5rem;
    }
    [data-testid="stMetricLabel"] {
        font-family: 'IBM Plex Mono', monospace;
        color: #888888;
        font-size: 0.75rem;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Onglets sobres, soulignement noir */
    button[data-baseweb="tab"] {
        font-family: 'Inter', sans-serif;
        font-weight: 500;
        font-size: 0.95rem;
        color: #999999;
    }
    button[data-baseweb="tab"][aria-selected="true"] { color: #111111; }
    div[data-baseweb="tab-highlight"] { background-color: #111111; }

    /* Graphiques : cadre fin, pas d'ombre */
    div[data-testid="stPlotlyChart"] {
        background-color: #FFFFFF;
        border: 1px solid #EAEAEA;
        padding: 1rem;
    }

    div[data-testid="stDataFrame"] { font-family: 'IBM Plex Mono', monospace; }

    .block-container { padding-top: 2rem; padding-bottom: 3rem; }
    hr { border-color: #EAEAEA; }
</style>
""", unsafe_allow_html=True)

st.title("Analyse des ventes retail — Walmart")
st.markdown("<p class='subtitle'>Exploration des ventes hebdomadaires de 45 magasins</p>", unsafe_allow_html=True)

# Palette noir/blanc/gris, un seul accent
COLORS = {"A": "#111111", "B": "#888888", "C": "#CCCCCC"}
PLOTLY_LAYOUT = dict(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(family="IBM Plex Mono, monospace", color="#111111", size=12),
    margin=dict(l=10, r=10, t=20, b=10),
)

@st.cache_data
def get_data():
    stores, features, sales = load_data()
    sales_clean = sales[sales["weekly_sales"] > 0]
    sales_merged = sales_clean.merge(stores, on="store", how="left")
    features_light = features.drop(columns=["isholiday"])
    full_data = sales_merged.merge(features_light, on=["store", "date"], how="left")
    full_data["date"] = pd.to_datetime(full_data["date"])
    full_data["has_promo"] = full_data["markdown1"].notna()
    return full_data

full_data = get_data()

# --- Sidebar : filtres ---
st.sidebar.header("Filtres")
store_types = st.sidebar.multiselect(
    "Type de magasin",
    options=sorted(full_data["type"].unique()),
    default=sorted(full_data["type"].unique())
)
date_min, date_max = full_data["date"].min(), full_data["date"].max()
date_range = st.sidebar.date_input("Période", value=(date_min, date_max), min_value=date_min, max_value=date_max)

filtered = full_data[full_data["type"].isin(store_types)]
if len(date_range) == 2:
    start, end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
    filtered = filtered[(filtered["date"] >= start) & (filtered["date"] <= end)]

# --- KPIs ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Ventes totales", f"${filtered['weekly_sales'].sum():,.0f}")
col2.metric("Ventes moy. / semaine", f"${filtered['weekly_sales'].mean():,.0f}")
col3.metric("Magasins", f"{filtered['store'].nunique()}")
col4.metric("Lignes analysées", f"{len(filtered):,}")

st.write("")

# --- Onglets ---
tab1, tab2, tab3 = st.tabs(["Évolution des ventes", "Saisonnalité & promotions", "Départements"])

with tab1:
    st.write("")
    weekly_by_type = filtered.groupby(["date", "type"])["weekly_sales"].sum().reset_index()
    fig1 = px.line(
        weekly_by_type, x="date", y="weekly_sales", color="type",
        color_discrete_map=COLORS,
        labels={"weekly_sales": "Ventes ($)", "date": "", "type": "Type"}
    )
    fig1.update_layout(**PLOTLY_LAYOUT, hovermode="x unified")
    fig1.update_traces(line=dict(width=2))
    st.plotly_chart(fig1, use_container_width=True)

with tab2:
    st.write("")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Effet des fêtes**")
        holiday_effect = filtered.groupby(["type", "isholiday"])["weekly_sales"].mean().reset_index()
        pivot = holiday_effect.pivot(index="type", columns="isholiday", values="weekly_sales")
        if True in pivot.columns and False in pivot.columns:
            pivot["% augmentation"] = ((pivot[True] - pivot[False]) / pivot[False] * 100).round(1)
            fig2 = go.Figure(go.Bar(
                x=pivot.index, y=pivot["% augmentation"],
                marker_color=[COLORS.get(t, "#111111") for t in pivot.index],
                text=pivot["% augmentation"].astype(str) + "%",
                textposition="outside"
            ))
            fig2.update_layout(**PLOTLY_LAYOUT, yaxis_title="% d'augmentation", xaxis_title="")
            st.plotly_chart(fig2, use_container_width=True)

    with col_b:
        st.markdown("**Effet des promotions**")
        promo_effect = filtered.groupby("has_promo")["weekly_sales"].mean().reset_index()
        promo_effect["has_promo"] = promo_effect["has_promo"].map({True: "Avec promo", False: "Sans promo"})
        fig3 = go.Figure(go.Bar(
            x=promo_effect["has_promo"], y=promo_effect["weekly_sales"],
            marker_color=["#CCCCCC", "#111111"],
            text=promo_effect["weekly_sales"].round(0),
            textposition="outside"
        ))
        fig3.update_layout(**PLOTLY_LAYOUT, yaxis_title="Ventes moyennes ($)", xaxis_title="")
        st.plotly_chart(fig3, use_container_width=True)

with tab3:
    st.write("")
    top_depts = filtered.groupby("dept")["weekly_sales"].sum().sort_values(ascending=False).head(10).reset_index()
    top_depts["dept"] = top_depts["dept"].astype(str)
    fig4 = px.bar(
        top_depts.sort_values("weekly_sales"), x="weekly_sales", y="dept", orientation="h",
        labels={"weekly_sales": "Ventes cumulées ($)", "dept": "Département"},
        color_discrete_sequence=["#111111"]
    )
    fig4.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig4, use_container_width=True)

st.write("")
with st.expander("Voir un extrait des données"):
    st.dataframe(filtered.head(10))