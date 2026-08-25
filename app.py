import streamlit as st
from data_loader import load_data
import pandas as pd
import matplotlib.pyplot as plt

st.set_page_config(page_title="Walmart Retail Analysis", layout="wide")

st.title("📊 Analyse des ventes retail — Walmart")
st.markdown("Exploration des ventes hebdomadaires de 45 magasins, croisées avec la saisonnalité et des facteurs externes.")

@st.cache_data
def get_data():
    stores, features, sales = load_data()
    sales_clean = sales[sales["weekly_sales"] > 0]
    sales_merged = sales_clean.merge(stores, on="store", how="left")
    return sales_merged

sales_merged = get_data()

st.write(f"**{len(sales_merged):,} lignes de ventes** après nettoyage")
st.dataframe(sales_merged.head(10))

weekly_by_type = sales_merged.groupby(["date", "type"])["weekly_sales"].sum().reset_index()

fig, ax = plt.subplots(figsize=(12, 6))
for store_type in ["A", "B", "C"]:
    data = weekly_by_type[weekly_by_type["type"] == store_type]
    ax.plot(data["date"], data["weekly_sales"], label=f"Type {store_type}")

ax.set_title("Évolution des ventes hebdomadaires par type de magasin")
ax.set_xlabel("Date")
ax.set_ylabel("Ventes hebdomadaires ($)")
ax.legend()
st.pyplot(fig)