import streamlit as st

# Page Configurations
st.set_page_config(
    page_title="CPU Scheduling Hub",
    page_icon="🖥️",
    layout="wide"
)

# Main Welcome Header
st.title("🖥️ CPU Scheduling Engine")
st.markdown("""
Welcome to the CPU Scheduling Hub. 
Select an option from the menu below.
""")

st.markdown("---")

# 🧭 RADIO BUTTON MENU WIDGET
option = st.radio(
    "🔍 Select a Destination:",
    options=[ 
        "Main Menu",
        "Round Robin (RR) Scheduler", 
        "Shortest Job First (SJF) Scheduler",
        "First Come First serve Scheduler (FCFS)",
        "View Round Robin Database History",
        "View SJF Database History",
        "View FCFS Database History"
    ],
    index=0,  
    horizontal=False # Stacked vertically for clean reading.
)

# 🔄 REDIRECTION LOGIC BASED ON RADIO SELECTION
if option == "Round Robin (RR) Scheduler":
    st.switch_page("pages/1_Round_Robin.py")

elif option == "Shortest Job First (SJF) Scheduler":
    st.switch_page("pages/2_Shortest_Job_First.py")

elif option == "First Come First serve Scheduler (FCFS)":
    st.switch_page("pages/3_First_Come_First_serve.py")

elif option == "View Round Robin Database History":
    st.switch_page("pages/4_RR_Database.py")

elif option == "View SJF Database History":
    st.switch_page("pages/5_SJF_Database.py")

elif option == "View FCFS Database History":
    st.switch_page("pages/6_FCFS_Database.py")


st.markdown("---")

# Quick Reference Context Columns
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("### 🔄 Round Robin (RR)")
    st.write("Allocates equal fixed time slices (Time Quantums) to every thread in a cyclic Ready Queue structure.")

with col2:
    st.markdown("### ⏱️ Shortest Job First (SJF)")
    st.write("Selects and executes the thread with the shortest upcoming expected CPU burst time remaining.")

with col3:
    st.markdown("### ⚡ First-Come, First-Served (FCFS)")
    st.write("Executes threads strictly in the order they arrive in the Ready Queue. Simple, non-preemptive scheduling.")