import sqlite3
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Database History", layout="wide")

class DatabaseManager:
    def __init__(self, db_name="scheduler_history.db"):
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS simulation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    process_name TEXT,
                    arrival_time INTEGER,
                    burst_time INTEGER,
                    completion_time INTEGER,
                    turnaround_time INTEGER,
                    waiting_time INTEGER
                )
            """)
            conn.commit()

    def fetch_history(self) -> pd.DataFrame:
        with sqlite3.connect(self.db_name) as conn:
            return pd.read_sql_query("SELECT * FROM simulation_history ORDER BY timestamp DESC", conn)

    def clear_history(self):
        with sqlite3.connect(self.db_name) as conn:
            conn.cursor().execute("DELETE FROM simulation_history")
            conn.commit()

# Main UI layout execution
st.title("📜 Database History Logs for Round Robin Scheduling")
st.markdown("Review past Round Robin Process scheduling configurations and calculated step outcomes here.")

db_mgr = DatabaseManager()
df_history = db_mgr.fetch_history()

if not df_history.empty:
    col1, _ = st.columns([1, 4])
    if col1.button("🗑️ Clear All History", type="secondary"):
        db_mgr.clear_history()
        st.success("Database history has been cleared.")
        st.rerun()

    st.write("### Simulation Audit Log Table")
    st.dataframe(df_history, use_container_width=True)
else:
    st.info("The database is empty. Execute a simulation run on the main dashboard tab.")