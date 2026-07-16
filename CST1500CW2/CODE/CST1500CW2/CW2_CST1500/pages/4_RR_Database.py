import sqlite3
import streamlit as st
import pandas as pd
import datetime

#  Database Management and Logic Layer(OOP)
class RRDatabaseViewer:
    def __init__(self, db_name="RR_scheduler_history.db"):
        self.db_name = db_name

    def get_all_run_tables(self) -> list:
        """Queries the database schema to locate all isolated RR tables."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'run_RR_Table_%'")
                tables = [row[0] for row in cursor.fetchall()]
                
                # Sort them numerically descending so the newest run is first
                tables.sort(key=lambda x: int(x.split("_")[-1]), reverse=True)
                return tables
        except Exception as e:
            st.error(f"Database extraction connection error: {e}")
            return []
        
    def fetch_run_metadata(self, table_name: str) -> dict:
        """Fetches the metrics snapshot for a specific run table from the run_index."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                # Ensure the master history index tracking infrastructure exists first
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS run_index (
                        run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        table_name TEXT,
                        avg_waiting REAL,
                        avg_turnaround REAL,
                        timestamp DATETIME
                    )
                """)
                cursor.execute(
                    "SELECT avg_waiting, avg_turnaround, timestamp FROM run_index WHERE table_name = ?", 
                    (table_name,)
                )
                row = cursor.fetchone()
                if row:
                    return {
                        "avg_waiting": row[0],
                        "avg_turnaround": row[1],
                        "timestamp": row[2]
                    }
        except Exception:
            pass
        return None

    def fetch_table_data(self, table_name: str) -> pd.DataFrame:
        """Reads data matrix frames securely from a specific isolated table."""
        with sqlite3.connect(self.db_name) as conn:
            return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

    def delete_all_history(self, tables_to_drop: list):
        """Iterates through and purges tracking logs from the system storage layer."""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            for table in tables_to_drop:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
            conn.commit()
    def export_csv_data(self, all_tables: list) -> str:
        """Combines all isolated tables into a single CSV string formatted for downloading."""
        all_data = []
        with sqlite3.connect(self.db_name) as conn:
            for table in all_tables:
                df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                run_num = table.split('_')[-1]
                
                
                df["run_table"] = table
                df["run_index_number"] = f"Run #{run_num}"
                if "timestamp" in df.columns:
                    df["run_timestamp"] = df["timestamp"]
                
                all_data.append(df)
                
        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            # Scrub out internal database layout tracking tags before exporting
            final_df = final_df.drop(columns=["id", "timestamp"], errors="ignore")
            return final_df.to_csv(index=False)
        return ""


# 🖥️ INTERACTION & PRESENTATION LAYER
def run_database_app():
    st.set_page_config(page_title="RR Database History", layout="wide")
    
    if st.button("⬅️ Back to Main Menu"):
        st.switch_page("Main_Menu.py")

    st.title("🗄️ Round Robin Scheduling Process History")
    st.markdown("Inspect performance analytics across individual or multiple simulation runs.")

    # Instantiate the OOP Viewer object
    viewer = RRDatabaseViewer()
    tables = viewer.get_all_run_tables()

    # Database Management Action UI Element
    st.markdown("### ⚙️ Database Management")
    if not tables:
        st.info("ℹ️ No results found. Run a simulation and save the results first!")
        return  

    # Clear history button logic
    col1, col2 = st.columns([1, 1])

    with col1:
        # confirmation box to confirm deletion
        confirm_clear = st.checkbox("Confirm clear history?")
        # clear all history button
        if st.button("🗑️ Clear All History", type="secondary", key="clear_rr"):
            if confirm_clear:
                viewer.delete_all_history(tables)
                st.success("Database history has been cleared.")
                st.rerun()
            else:
                st.warning("Please tick the confirmation box before clearing.")

    with col2:
        # Export History Action UI Element matching the layout position
        csv_data = viewer.export_csv_data(tables)
        if csv_data:
            st.write("") # Spacer to align nicely with the button layout
            st.download_button(
                label="📤 Export History to CSV",
                data=csv_data,
                file_name="round_robin_history_export.csv",
                mime="text/csv",
                type="primary"
            )
    # Build the choices dropdown, injecting the "ALL" option at the top
    options_list = ["ALL_RUNS"] + tables
    display_options = {t: f"🏆 Simulation Run #{t.split('_')[-1]}" for t in tables}
    display_options["ALL_RUNS"] = "📊 Show All Tables"
    
    selected_table_raw = st.selectbox(
        "🔍 Select a Simulation Run to Inspect:",
        options=options_list,
        format_func=lambda x: display_options[x]
    )
    
    st.markdown("---")
    
    
    if selected_table_raw == "ALL_RUNS":
        st.subheader("📊 All Simulation Runs")
        
        # Loop through each table and render them one by one, keeping them unmerged
        for table in tables:
            run_num = table.split('_')[-1]
            df_raw = viewer.fetch_table_data(table)
            
            st.markdown(f"### Table {run_num}")
            meta = viewer.fetch_run_metadata(table)
            if meta:
                avg_waiting = float(meta["avg_waiting"])
                avg_turnaround = float(meta["avg_turnaround"])
                ts = meta["timestamp"]
                try:
                    dt_obj = datetime.datetime.fromisoformat(ts)
                    formatted = dt_obj.strftime("%A, %d %B %Y at %I:%M %p")
                except Exception:
                    formatted = ts
            else:
                # Dynamic fallback calculations if metadata table missing
                avg_waiting = df_raw["Waiting Time"].mean() if "Waiting Time" in df_raw.columns else 0.0
                avg_turnaround = df_raw["Turnaround Time"].mean() if "Turnaround Time" in df_raw.columns else 0.0
                formatted = "Stored in Session log"

            # Render metrics side-by-side above individual loop tables
            m_col1, m_col2 = st.columns(2)
            m_col1.metric("Average Waiting Time", f"{avg_waiting:.2f} s")
            m_col2.metric("Average Turnaround Time", f"{avg_turnaround:.2f} s")
            st.caption(f"📅 **Execution Date & Time:** {formatted}")
            
            # Hide internal columns not meant for end-user viewing
            df_clean = df_raw.drop(columns=["id", "timestamp"], errors="ignore")
            st.dataframe(df_clean, use_container_width=True)
            st.markdown("---")
            
    else:
        # Display just the single chosen table
        run_num = selected_table_raw.split('_')[-1]
        df_raw = viewer.fetch_table_data(selected_table_raw)

        st.subheader(f"📋 Results for Run {run_num}")

        
        meta = viewer.fetch_run_metadata(selected_table_raw)
        if meta:
            avg_waiting, avg_turnaround, ts = meta
            try:
                dt_obj = datetime.datetime.fromisoformat(ts)
                formatted = dt_obj.strftime("%A, %d %B %Y at %I:%M %p")
            except Exception:
                formatted = ts
        else:
            avg_waiting = df_raw["Waiting Time"].mean() if "Waiting Time" in df_raw.columns else 0.0
            avg_turnaround = df_raw["Turnaround Time"].mean() if "Turnaround Time" in df_raw.columns else 0.0
            formatted = "Stored in Session log"

        # Render metrics side-by-side above single run tables
        col1, col2 = st.columns(2)
        col1.metric("Average Waiting Time", f"{avg_waiting:.2f} s")
        col2.metric("Average Turnaround Time", f"{avg_turnaround:.2f} s")
        st.caption(f"📅 **Execution Date & Time:** {formatted}")
        st.markdown("<br>", unsafe_allow_html=True)
            
        df_clean = df_raw.drop(columns=["id", "timestamp"], errors="ignore")
        st.dataframe(df_clean, use_container_width=True)

# Ensures the app only runs when this file is executed directly
if __name__ == "__main__":
    run_database_app()