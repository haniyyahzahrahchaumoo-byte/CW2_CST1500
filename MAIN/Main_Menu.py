import streamlit as st

st.set_page_config(page_title="FCFS Project", layout="wide")

st.title("⚡ FCFS Scheduling Project")
st.markdown("""
Welcome to the First-Come-First-Served (FCFS) Scheduling Simulator.

Use the sidebar to navigate:
- **FCFS Scheduler** → Run simulations, view logs, results, and Gantt chart.
- **FCFS Database History** → Review past runs, clear history, or export to CSV.
""")
