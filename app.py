import streamlit as st
from data_loader import load_data
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Walmart Retail Analysis", page_icon="📊", layout="wide")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .main { background-color: #FAFAFA; padding-top: 1rem; }

    h1 { color: #1F3864; font-weight: 700; font-size: 2.2rem; letter-spacing: -0.02em; }
    h2, h3 { color: #1F3864; font-weight: 600; }
    p, span, div { font-family: 'Inter', sans-serif; }

    [data-testid="stSidebar"] { background-color: #F5F5F3; }
    [data-testid="stSidebar"] h2 { font-size: 1rem; text-transform: uppercase; letter-spacing: 0.05em; color: #595959; }

    /* Cartes KPI avec ombre légère */
    [data-testid="stMetric"] {
        background-color: white;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
        border: 1px solid #EEEEEE;
    }
    [data-testid="stMetricValue"] { color: #1F3864; font-weight: 700; font-size: 1.6rem; }
    [data-testid="stMetricLabel"] { color: #8A8A8A; font-size: 0.85rem; font-weight: 500; }

    /* Onglets plus espacés et sobres */
    button[data-baseweb="tab"] {
        font-weight: 600;
        font-size: 0.95rem;
        color: #8A8A8A;
    }
    button[data-baseweb="tab"][aria-selected="true"] { color: #1F3864; }
    div[data-baseweb="tab-highlight"] { background-color: #B08D57; }

    /* Conteneurs de graphiques avec carte */
    div[data-testid="stPlotlyChart"] {
        background-color: white;
        border-radius: 12px;
        padding: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
        border: 1px solid #EEEEEE;
    }

    div[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }

    .block-container { padding-top: 2rem; padding-bottom: 3rem; }
</style>
""", unsafe_allow_html=True)

st.title("Analyse des ventes retail — Walmart")
st.markdown("<p style='color:#8A8A8A; font-size:1.05rem; margin-bottom:2rem;'>Exploration des ventes hebdomadaires de 45 magasins, croisées avec la saisonnalité et des facteurs externes.</p>", unsafe_allow_html=True)

COLORS = {"A": "#1F3864", "B": "#B08D57", "C": "#8FA8C4"}
PLOTLY_LAYOUT = dict(
    plot_bgcolor="white",
    paper_bgcolor="white",
    font=dict(family="Inter, sans-serif", color="#262626", size=13),
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

st.write("")  # espacement

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
    fig1.update_traces(line=dict(width=2.5))
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
                marker_color=[COLORS.get(t, "#1F3864") for t in pivot.index],
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
            marker_color=["#8FA8C4", "#B08D57"],
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
        color_discrete_sequence=["#1F3864"]
    )
    fig4.update_layout(**PLOTLY_LAYOUT)
    st.plotly_chart(fig4, use_container_width=True)

st.write("")
with st.expander("Voir un extrait des données"):
    st.dataframe(filtered.head(10))