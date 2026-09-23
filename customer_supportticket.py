from pathlib import Path

import pandas as pd
import streamlit as st


st.set_page_config(page_title="Customer Support Ticket Classifier", page_icon="🎫", layout="wide")

DATA_PATH = Path(__file__).with_name("customer_support_ticket_dataset.csv")


@st.cache_data
def load_dataset():
    return pd.read_csv(DATA_PATH)


df = load_dataset()

# 2. Function to search details through ticket_id or customer_name
def customer_lookup(search):
    if not search:
        return df

    result = df[
         df['customer_name'].str.contains(search, case=False, na=False, regex=False)
         |
         df['ticket_id'].str.contains(search, case=False, na=False, regex=False)
    ]
    return result[
        ['ticket_id', 'customer_name', 'customer_tier', 'category', 'priority', 'sentiment', 'resolution_status', 'language', 'ticket_text']
    ]

# 3. Auto-responder function
def auto_responder(ticket_id):
    ticket = df[df['ticket_id'] == ticket_id]

    if ticket.empty:
        return 'Ticket not found'

    ticket = ticket.iloc[0]
    lang = ticket['language']
    name = ticket['customer_name']
    response = ticket['suggested_response']

    if lang == 'hi':
        return f'नमस्ते {name},\n\n{response}\n\nयदि आपको किसी और सहायता की आवश्यकता हो, तो कृपया हमें बताएं।'
    
    return f"Hello {name},\n\n{response}\n\nPlease let us know if you need any further assistance."

# 4. Ticket routing decision function
def route_ticket(ticket_id):
    ticket_rows = df[df['ticket_id'] == ticket_id]
    if ticket_rows.empty:
        return 'Ticket not found'
        
    ticket = ticket_rows.iloc[0]

    if ticket['priority'] == 'High' or ticket['sentiment'] == 'Negative' or ticket['priority'] == 'Urgent':
        return 'Human agent review required'

    return 'Auto-response eligible'

st.title("Customer Support Ticket Classifier")
st.caption("Search tickets, review their routing decision, and prepare an automatic response.")

total_tickets = len(df)
open_tickets = int((df["resolution_status"] != "Resolved").sum())
high_priority = int(df["priority"].isin(["High", "Urgent"]).sum())
resolved_rate = int((df["resolution_status"] == "Resolved").mean() * 100)

metric_one, metric_two, metric_three, metric_four = st.columns(4)
metric_one.metric("Total tickets", f"{total_tickets:,}")
metric_two.metric("Open tickets", f"{open_tickets:,}")
metric_three.metric("High priority", f"{high_priority:,}")
metric_four.metric("Resolved", f"{resolved_rate}%")

st.divider()

search_text = st.text_input(
    "Search by ticket ID or customer name",
    placeholder="Example: TKT-00004 or Ben",
)
category = st.selectbox("Filter by category", ["All categories"] + sorted(df["category"].unique()))

results = customer_lookup(search_text.strip())
if category != "All categories":
    results = results[results["category"] == category]

st.subheader(f"Matching tickets ({len(results)})")
if results.empty:
    st.warning("No matching tickets found.")
else:
    display_columns = [
        "ticket_id", "customer_name", "customer_tier", "category",
        "priority", "sentiment", "resolution_status",
    ]
    st.dataframe(results[display_columns], use_container_width=True, hide_index=True)

    selected_ticket_id = st.selectbox("Choose a ticket to inspect", results["ticket_id"].tolist())
    selected_ticket = df[df["ticket_id"] == selected_ticket_id].iloc[0]

    details, response = st.columns(2)
    with details:
        st.subheader("Ticket details")
        st.write(f"**Customer:** {selected_ticket['customer_name']}")
        st.write(f"**Channel:** {selected_ticket['channel']}")
        st.write(f"**Intent:** {selected_ticket['category']} / {selected_ticket['subcategory']}")
        st.write(f"**Priority:** {selected_ticket['priority']}")
        st.write(f"**Sentiment:** {selected_ticket['sentiment']}")
        st.write(f"**Status:** {selected_ticket['resolution_status']}")
        st.info(selected_ticket["ticket_text"])

    with response:
        st.subheader("Routing decision")
        routing = route_ticket(selected_ticket_id)
        if routing == "Human agent review required":
            st.error(routing)
        else:
            st.success(routing)

        st.subheader("Auto-response preview")
        response_text = auto_responder(selected_ticket_id)
        st.text_area("Response", response_text, height=180)
        st.download_button(
            "Download response",
            response_text,
            file_name=f"{selected_ticket_id}_response.txt",
            mime="text/plain",
        )