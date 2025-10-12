# dashboard/streamlit_app.py

import streamlit as st
import pandas as pd
import asyncio
import plotly.express as px
from datetime import datetime
import sys
from pathlib import Path

# Ensure project root is on path so we can import backend modules
project_root = str(Path(__file__).parent.parent)
if project_root not in sys.path:
    sys.path.append(project_root)

from backend.firebase_client import get_conversations, get_analytics_data

# --- Page configuration ---
st.set_page_config(page_title="FAQ Bot Dashboard", layout="wide")
st.title("📊 WhatsApp FAQ Bot Dashboard")
st.markdown("Manage and analyze WhatsApp conversations collected by the FAQ Bot.")

BUSINESS_ID_DEFAULT = "business_01"


# --- Helpers to call async backend functions from sync Streamlit ---
def fetch_conversations(business_id: str = BUSINESS_ID_DEFAULT, limit: int = 500) -> list:
    try:
        return asyncio.run(get_conversations(business_id=business_id, limit=limit))
    except Exception as e:
        st.error(f"Failed to fetch conversations: {e}")
        return []


def fetch_analytics(business_id: str = BUSINESS_ID_DEFAULT) -> dict:
    try:
        return asyncio.run(get_analytics_data(business_id=business_id))
    except Exception as e:
        st.error(f"Failed to fetch analytics: {e}")
        return {}


# --- Page: Home (metrics) ---
def page_home():
    st.header("Home — Key Metrics")
    analytics = fetch_analytics()
    conversations = fetch_conversations(limit=1000)

    col1, col2, col3, col4 = st.columns(4)
    total_queries = analytics.get("total_queries", len(conversations))
    top_queries_list = analytics.get("top_queries", [])
    query_type_counts = analytics.get("query_type_counts", {})

    unique_users = len(set([c.get("user_id") for c in conversations if c.get("user_id")]))

    col1.metric("Total Queries", total_queries)
    col2.metric("Unique Users", unique_users)
    avg_q_per_user = f"{(total_queries / unique_users):.2f}" if unique_users else "0"
    col3.metric("Avg Queries / User", avg_q_per_user)
    col4.metric("Query Types", ", ".join([f"{k}:{v}" for k, v in list(query_type_counts.items())[:3]]) or "n/a")

    st.subheader("Top Queries")
    if top_queries_list:
        df_top = pd.DataFrame(top_queries_list)
        st.table(df_top)
        fig = px.bar(df_top, x="query", y="count", title="Top Queries")
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("No top query data available yet.")

    st.markdown("---")
    st.markdown("Tip: Use the Conversations page to filter and explore individual messages.")


# --- Page: Analytics (charts) ---
def page_analytics():
    st.header("Analytics — Trends & Charts")
    conversations = fetch_conversations(limit=2000)
    if not conversations:
        st.warning("No conversation data available for analytics.")
        return

    df = pd.DataFrame(conversations)
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp'].dt.date
    else:
        st.warning("Timestamps missing from data; charts will be limited.")
        df['date'] = pd.NaT

    # Queries per day
    queries_per_day = df.groupby('date').size().reset_index(name='count')
    if not queries_per_day.empty:
        fig = px.line(queries_per_day, x='date', y='count', title='Queries per Day')
        st.plotly_chart(fig, width='stretch')
    else:
        st.info("Not enough data to plot queries per day.")

    # Query type distribution
    if 'query_type' in df.columns:
        qtype = df['query_type'].fillna('unknown').value_counts().reset_index()
        qtype.columns = ['query_type', 'count']
        fig2 = px.pie(qtype, names='query_type', values='count', title='Query Type Distribution')
        st.plotly_chart(fig2, width='stretch')
    else:
        st.info("No query_type field available in data.")


# --- Page: Conversations (viewer with filters) ---
def page_conversations():
    st.header("Conversations — Viewer")

    conversations = fetch_conversations(limit=2000)
    if not conversations:
        st.warning("No conversations to display.")
        return

    df = pd.DataFrame(conversations)

    # Normalize timestamp
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    else:
        df['timestamp'] = pd.NaT

    # Shorten user_id display
    if 'user_id' in df.columns:
        df['short_user'] = df['user_id'].astype(str).str.replace('whatsapp:', '', regex=False)
    else:
        df['short_user'] = ""

    # Filters
    st.sidebar.subheader("Filters")
    min_date = df['timestamp'].min()
    max_date = df['timestamp'].max()
    try:
        default_start = min_date.date() if pd.notna(min_date) else datetime.now().date()
        default_end = max_date.date() if pd.notna(max_date) else datetime.now().date()
    except Exception:
        default_start = default_end = datetime.now().date()
    date_range = st.sidebar.date_input("Date range", value=(default_start, default_end))

    query_types = df['query_type'].dropna().unique().tolist() if 'query_type' in df.columns else []
    selected_types = st.sidebar.multiselect("Query types", options=query_types, default=query_types)

    search_text = st.sidebar.text_input("Search text (query/answer)")

    # Apply filters
    filtered = df.copy()
    if isinstance(date_range, (list, tuple)) and len(date_range) == 2 and pd.notna(filtered['timestamp']).any():
        start, end = date_range
        filtered = filtered[(filtered['timestamp'].dt.date >= start) & (filtered['timestamp'].dt.date <= end)]

    if selected_types:
        filtered = filtered[filtered['query_type'].isin(selected_types)]

    if search_text:
        mask = filtered.astype(str).apply(lambda row: row.str.contains(search_text, case=False, na=False)).any(axis=1)
        filtered = filtered[mask]

    st.info(f"Showing {len(filtered)} of {len(df)} conversations after filters.")
    display_cols = ['timestamp', 'short_user', 'query_type', 'query', 'transcription', 'answer']
    display_cols = [c for c in display_cols if c in filtered.columns]
    if 'timestamp' in display_cols:
        filtered = filtered.sort_values(by='timestamp', ascending=False)
    st.dataframe(filtered[display_cols].reset_index(drop=True), width='stretch')

    # CSV download
    csv = filtered.to_csv(index=False).encode('utf-8')
    st.download_button("Download filtered CSV", data=csv, file_name="conversations.csv", mime="text/csv")


# --- Page: PDF Manager (simple link) ---
def page_pdf_manager():
    st.header("PDF Manager")
    st.markdown("Manage uploaded PDFs and FAISS indexes.")
    st.markdown("This project includes a `business/upload-pdf` endpoint to upload brochures and create FAISS indexes.")
    st.markdown("For advanced PDF management, consider adding an upload UI and index status indicators here.")


# --- Navigation ---
PAGES = {
    "Home": page_home,
    "Analytics": page_analytics,
    "Conversations": page_conversations,
    "PDF Manager": page_pdf_manager,
}

st.sidebar.title("Navigation")
selected = st.sidebar.radio("Go to", list(PAGES.keys()), index=0)
# Ensure selected is never None for type-checkers
selected = selected or list(PAGES.keys())[0]

# Optional business selector
business_id = st.sidebar.text_input("Business ID", value=BUSINESS_ID_DEFAULT)

# Run selected page
page_fn = PAGES.get(selected)
if page_fn:
    page_fn()