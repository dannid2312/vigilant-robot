import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st
import matplotlib.pyplot as plt
from babel.numbers import format_currency

sns.set(style='dark')

st.header(':sparkles: E-Commerce Dataset Review :sparkles:')

all_df = pd.read_csv('data.csv')
all_df['order_purchase_timestamp'] = pd.to_datetime(all_df['order_purchase_timestamp'])
print(all_df.info())

min_date = all_df["order_purchase_timestamp"].min()
max_date = all_df["order_purchase_timestamp"].max()

with st.sidebar:
    # Mengambil start_date & end_date dari date_input
    start_date, end_date = st.date_input(
        label='Rentang Waktu', min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

print(start_date, end_date)
main_df = all_df[(all_df["order_purchase_timestamp"] >= pd.to_datetime(start_date)) &
                 (all_df["order_purchase_timestamp"] < pd.to_datetime(end_date) + pd.Timedelta(days=1))]
print(main_df.info())
print(
main_df["order_purchase_timestamp"].min(),
main_df["order_purchase_timestamp"].max()
)

st.subheader('Top 10 Product Categories based on Order Count and Average Review Score')

# Calculate order count and average review score per product category
category_order_count = main_df.groupby('product_category_name')['order_id'].nunique()
category_avg_review = main_df.groupby('product_category_name')['review_score'].mean()

# Select top 10 product categories by order count
top_10_categories = category_order_count.sort_values(ascending=False).head(15).index

# Filter data for the top 10 categories
category_order_count = category_order_count[top_10_categories]
category_avg_review = category_avg_review[top_10_categories]

# Create dual axis plot
fig, ax1 = plt.subplots(figsize=(12, 6))

# Bar plot for order count
ax1.bar(top_10_categories, category_order_count, color='skyblue')
ax1.set_xlabel("Product Category")
ax1.set_ylabel("Order Count", color='skyblue')
ax1.tick_params(axis='y', labelcolor='skyblue')
ax1.set_xticklabels(top_10_categories, rotation=45, ha='right')

# Line plot for average review score on the second y-axis
ax2 = ax1.twinx()
ax2.plot(top_10_categories, category_avg_review, color='orange', marker='o')
ax2.set_ylabel("Average Review Score", color='orange')
ax2.tick_params(axis='y', labelcolor='orange')

plt.tight_layout()
st.pyplot(fig)

filtered_df = main_df[main_df['order_status']=='delivered'][['customer_unique_id','price','freight_value','order_purchase_timestamp','order_id']].drop_duplicates()
filtered_df['total_price'] = filtered_df['price'] + filtered_df['freight_value']

rfm = filtered_df.groupby(by='customer_unique_id', as_index=False).agg({
    "order_purchase_timestamp": "max", # mengambil tanggal pemesanan terakhir
    "order_id": "nunique", # menghitung jumlah order yang dilakukan pelanggan
    "total_price": "sum" # menghitung jumlah uang yang dikeluarkan pelanggan
    })

rfm.columns = ["customer_unique_id", "max_order_timestamp", "frequency", "monetary"]
customer_unique_id_mapping = {unique_id: str(i) for i, unique_id in enumerate(rfm['customer_unique_id'].unique())}
rfm['customer_encoded_id'] = rfm['customer_unique_id'].map(customer_unique_id_mapping) #mempersingkat customer_unique_id

rfm["max_order_timestamp"] = pd.to_datetime(rfm["max_order_timestamp"])
recent_date = rfm["max_order_timestamp"].max() + pd.Timedelta(days=1)
rfm["recency"] = rfm["max_order_timestamp"].apply(lambda x: (recent_date - x).days)

rfm = rfm[['customer_unique_id','customer_encoded_id','recency','frequency','monetary']]

st.subheader("Best Customer based on RFM Analysis using encoded_customer_id")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_monetary = format_currency(rfm.monetary.mean(),
                                   "BRL", locale="pt_BR")
    st.metric("Average Monetary", value=avg_monetary)

# Data preparation (assuming rfm_customer DataFrame is already created)
recency_data = rfm.sort_values(by="recency", ascending=True).head(5)
frequency_data = rfm.sort_values(by="frequency", ascending=False).head(5)
monetary_data = rfm.sort_values(by="monetary", ascending=False).head(5)

# Create figure and axes
colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(30, 6))

# Recency Plot (ax[0])
ax[0].bar(x=recency_data['customer_encoded_id'], height=recency_data['recency'], color=colors)
ax[0].set_title("By Recency (days)", loc="center", fontsize=18)
ax[0].set_ylabel("Recency (days)")
ax[0].tick_params(axis='x', labelsize=15)

# Frequency Plot (ax[1])
ax[1].bar(frequency_data['customer_encoded_id'], frequency_data['frequency'], color=colors)
ax[1].set_title("By Frequency", loc="center", fontsize=18)
ax[1].set_ylabel("Frequency")
ax[1].tick_params(axis='x', labelsize=15)

# Monetary Plot (ax[2])
ax[2].bar(monetary_data['customer_encoded_id'], monetary_data['monetary'], color=colors)
ax[2].set_title("By Monetary", loc="center", fontsize=18)
ax[2].set_ylabel("Monetary")
ax[2].tick_params(axis='x', labelsize=15)

# Show the plot
st.pyplot(fig)
