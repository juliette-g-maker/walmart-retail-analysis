import streamlit as st
from data_loader import load_data
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Walmart Retail Analysis", page_icon="📊", layout="wide")

# --- CSS personnalisé : palette sobre, typographie propre ---
st.markdown("""
<style>
    .main { background-color: #FAFAFA; }
    h1 { color: #1F3864; font-weight: 700; }
    h2, h3 { color: #1F3864; font-weight: 600; margin-top: 2rem; }
    [data-testid="stMetricValue"] { color: #1F3864; font-weight: 700; }
    [data-testid="stMetricLabel"] { color: #595959; }
    [data-testid="stSidebar"] { background-color: #F2F2F2; }
    div[data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
    hr { margin: 2rem 0; border-color: #E0E0E0; }
</style>
""", unsafe_allow_html=True)

st.title("Analyse des ventes retail — Walmart")
st.markdown("<p style='color:#595959; font-size:1.05rem;'>Exploration des ventes hebdomadaires de 45 magasins, croisées avec la saisonnalité et des facteurs externes.</p>", unsafe_allow_html=True)

@st.cache_data
def get_data():
    stores, features, sales = load_data()
    sales_clean = sales[sales["weekly_sales"] > 0]
    sales_merged = sales_clean.merge(stores, on="store", how="left")
    full_data = sales_merged.merge(features, on=["store", "date"], how="left")
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

full_data["date"] = pd.to_datetime(full_data["date"])
filtered = full_data[full_data["type"].isin(store_types)]
if len(date_range) == 2:
    start = pd.Timestamp(date_range[0])
    end = pd.Timestamp(date_range[1])
    filtered = filtered[(filtered["date"] >= start) & (filtered["date"] <= end)]

# --- KPIs en haut ---
col1, col2, col3, col4 = st.columns(4)
col1.metric("Ventes totales", f"${filtered['weekly_sales'].sum():,.0f}")
col2.metric("Ventes moy. / semaine", f"${filtered['weekly_sales'].mean():,.0f}")
col3.metric("Magasins", f"{filtered['store'].nunique()}")
col4.metric("Lignes analysées", f"{len(filtered):,}")

st.markdown("<hr>", unsafe_allow_html=True)

# --- Palette pour les graphiques ---
COLORS = {"A": "#1F3864", "B": "#B08D57", "C": "#8FA8C4"}

# --- Graphique 1 ---
st.subheader("Évolution des ventes par type de magasin")
weekly_by_type = filtered.groupby(["date", "type"])["weekly_sales"].sum().reset_index()
fig1, ax1 = plt.subplots(figsize=(12, 4.5))
for store_type in store_types:
    data = weekly_by_type[weekly_by_type["type"] == store_type]
    ax1.plot(data["date"], data["weekly_sales"], label=f"Type {store_type}", color=COLORS.get(store_type), linewidth=2)
ax1.spines["top"].set_visible(False)
ax1.spines["right"].set_visible(False)
ax1.set_ylabel("Ventes ($)")
ax1.legend(frameon=False)
st.pyplot(fig1)

st.markdown("<hr>", unsafe_allow_html=True)

# --- Effet saisonnier + promotions côte à côte ---
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Effet des fêtes")
    holiday_effect = filtered.groupby(["type", "isholiday"])["weekly_sales"].mean().reset_index()
    pivot = holiday_effect.pivot(index="type", columns="isholiday", values="weekly_sales")
    if True in pivot.columns and False in pivot.columns:
        pivot["% augmentation"] = ((pivot[True] - pivot[False]) / pivot[False] * 100).round(1)
        fig2, ax2 = plt.subplots(figsize=(5.5, 4))
        bars = ax2.bar(pivot.index, pivot["% augmentation"], color=[COLORS.get(t, "#1F3864") for t in pivot.index])
        ax2.spines["top"].set_visible(False)
        ax2.spines["right"].set_visible(False)
        ax2.set_ylabel("% d'augmentation")
        st.pyplot(fig2)

with col_b:
    st.subheader("Effet des promotions")
    promo_effect = filtered.groupby("has_promo")["weekly_sales"].mean().reset_index()
    promo_effect["has_promo"] = promo_effect["has_promo"].map({True: "Avec promo", False: "Sans promo"})
    fig3, ax3 = plt.subplots(figsize=(5.5, 4))
    ax3.bar(promo_effect["has_promo"], promo_effect["weekly_sales"], color=["#8FA8C4", "#B08D57"])
    ax3.spines["top"].set_visible(False)
    ax3.spines["right"].set_visible(False)
    ax3.set_ylabel("Ventes moyennes ($)")
    st.pyplot(fig3)

st.markdown("<hr>", unsafe_allow_html=True)

# --- Top départements ---
st.subheader("Top 10 des départements")
top_depts = filtered.groupby("dept")["weekly_sales"].sum().sort_values(ascending=False).head(10)
fig4, ax4 = plt.subplots(figsize=(10, 4.5))
ax4.barh(top_depts.index.astype(str), top_depts.values, color="#1F3864")
ax4.invert_yaxis()
ax4.spines["top"].set_visible(False)
ax4.spines["right"].set_visible(False)
ax4.set_xlabel("Ventes cumulées ($)")
st.pyplot(fig4)

with st.expander("Voir un extrait des données"):
    st.dataframe(filtered.head(10))