import sqlite3
import streamlit as st
import pandas as pd

#  DATABASE MANAGEMENT
class DatabaseManager:
    def __init__(self, db_name="FCFS_scheduler_history.db"):
        self.db_name = db_name

    def _get_next_table_number(self, cursor, algorithm_name: str) :


        prefix = f"run_{algorithm_name}_%"
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?", (prefix,))
        existing_tables = cursor.fetchall()


        return len(existing_tables) + 1

    def save_results(self, df_results: pd.DataFrame, algorithm_name: str, avg_waiting: float, avg_turnaround: float):


        df_to_save = df_results.rename(columns={
            "Process Number": "process_name",
            "Burst Time": "burst_time",
            "Completion Time": "completion_time",
            "Turnaround Time": "turnaround_time",
            "Waiting Time": "waiting_time"
        }).copy()

        df_to_save["avg_waiting_time"] = avg_waiting
        df_to_save["avg_turnaround_time"] = avg_turnaround

        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            # Calculate the next sequential number
            table_num = self._get_next_table_number(cursor, algorithm_name)
            unique_table_name = f"run_{algorithm_name}_Table_{table_num}"


            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {unique_table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    process_name TEXT,
                    burst_time INTEGER,
                    completion_time INTEGER,
                    turnaround_time INTEGER,
                    waiting_time INTEGER,
                    avg_waiting_time REAL,
                    avg_turnaround_time REAL
                )
            """)

            df_to_save.to_sql(unique_table_name, conn, if_exists="replace", index=False)

        return unique_table_name


class FCFSDatabaseViewer:
    '''
    This class retrieves and displays previously saved     simulation runs, allowing users to:

    - Browse all historical simulations
    - View details of individual runs
    - Export data as csv file for external analysis
    - Clear old results to manage database
    '''
    def __init__(self, db_name="FCFS_scheduler_history.db"):
        self.db_name = db_name

    def get_all_run_tables(self) :
        """Queries the database schema to locate all isolated FCFS tables."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'run_FCFS_Table_%'")
                tables = [row[0] for row in cursor.fetchall()]

                # Sort them numerically descending so the newest run is displayed first
                tables.sort(key=lambda x: int(x.split("_")[-1]), reverse=True)
                # returns list of table names
                return tables
        except Exception as e:
            st.error(f"Database extraction connection error: {e}")
            return []

    def fetch_table_data(self, table_name: str) :
        """Retrieves data from a specific simulation run results table"""
        with sqlite3.connect(self.db_name) as conn:
            return pd.read_sql_query(f"SELECT * FROM {table_name}", conn)

    def delete_all_history(self, tables_to_drop: list):
        """ Permanently delete all specified simulation results table from database"""
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            for table in tables_to_drop:
                cursor.execute(f"DROP TABLE IF EXISTS {table}")
            conn.commit()

    def export_csv_data(self, all_tables: list):
        """Combines all isolated tables into a single CSV string formatted for downloading."""
        all_data = []
        with sqlite3.connect(self.db_name) as conn:
            for table in all_tables:
                df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                # extracts run number from table name
                run_num = table.split('_')[-1]

                # adds metadata columns
                df["run_table"] = table
                df["run_index_number"] = f"Run #{run_num}"
                if "timestamp" in df.columns:
                    df["run_timestamp"] = df["timestamp"]

                all_data.append(df)

        # combines all dataframes into single export
        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            # Scrub out internal database layout tracking tags before exporting
            final_df = final_df.drop(columns=["id", "timestamp"], errors="ignore")
            return final_df.to_csv(index=False)
        return ""


#  INTERACTION & PRESENTATION LAYER
def run_database_app():
    st.set_page_config(page_title="FCFS Database History", layout="wide")

    if st.button("⬅️ Back to Main Menu"):
        st.switch_page("Main_Menu.py")

    st.title("🗄️ First Come First Serve Scheduling Process History")
    st.markdown("Inspect performance analytics across individual or multiple simulation runs.")

    # Retrieves all historical simulation tables
    viewer = FCFSDatabaseViewer()
    tables = viewer.get_all_run_tables()


    st.markdown("### ⚙️ Database Management")
    if not tables:
        st.info("ℹ️ No results found. Run a simulation and save the results first!")
        return

    # Clear history and Export side by side layout
    col1, col2 = st.columns([1, 1])

    with col1:
        # confirmation box to confirm deletion
        confirm_clear = st.checkbox("Confirm clear history?")
        # clear all history button
        if st.button("🗑️ Clear All FCFS History", type="secondary"):
            if confirm_clear:
                viewer.delete_all_history(tables)
                st.success("🎉 All First Come First Serve tables cleared successfully!")
                st.rerun()
            else:
                st.warning("Please tick the confirmation box before clearing.")

    with col2:
        # Generate CSV data from all tables
        csv_data = viewer.export_csv_data(tables)
        if csv_data:
            st.download_button(
                label="📤 Export All History to CSV",
                data=csv_data,
                file_name="fcfs_history_export.csv",
                mime="text/csv",
                type="primary"
            )
        else:
            st.info("No data to export.")

    st.markdown("---")

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

    # ─── DISPLAY LOGIC ───
    if selected_table_raw == "ALL_RUNS":
        st.subheader("📊 All Simulation Runs")

        # Loop through each table and render them one by one, keeping them unmerged
        for table in tables:
            run_num = table.split('_')[-1]
            df_raw = viewer.fetch_table_data(table)

            st.markdown(f"### Table {run_num}")
            avg_waiting = float(df_raw["avg_waiting_time"].iloc[0]) if "avg_waiting_time" in df_raw.columns else 0.0
            avg_turnaround = float(df_raw["avg_turnaround_time"].iloc[0]) if "avg_turnaround_time" in df_raw.columns else 0.0

            # Render summary cards side-by-side above individual table grids
            m_col1, m_col2 = st.columns(2)
            m_col1.metric("Average Waiting Time", f"{avg_waiting:.2f} s")
            m_col2.metric("Average Turnaround Time", f"{avg_turnaround:.2f} s")
            if "timestamp" in df_raw.columns:
                st.caption(f"📅 **Execution Date & Time:** {df_raw['timestamp'].iloc[0]}")

            df_clean = df_raw.drop(columns=["id", "timestamp"], errors="ignore")
            st.dataframe(df_clean, use_container_width=True)
            st.markdown("---")  # Visual divider between the tables

    else:
        # Display just the single chosen table
        run_num = selected_table_raw.split('_')[-1]
        df_raw = viewer.fetch_table_data(selected_table_raw)

        st.subheader(f"📋 Results for Run {run_num}")
        avg_waiting = float(df_raw["avg_waiting_time"].iloc[0]) if "avg_waiting_time" in df_raw.columns else 0.0
        avg_turnaround = float(df_raw["avg_turnaround_time"].iloc[0]) if "avg_turnaround_time" in df_raw.columns else 0.0

        # Render summary cards side-by-side above single run view table grid
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Average Waiting Time", f"{avg_waiting:.2f} s")
        col_m2.metric("Average Turnaround Time", f"{avg_turnaround:.2f} s")

        if "timestamp" in df_raw.columns:
            st.caption(f"📅 **Execution Date & Time:** {df_raw['timestamp'].iloc[0]}")

        df_clean = df_raw.drop(columns=["id", "timestamp"], errors="ignore")
        st.dataframe(df_clean, use_container_width=True)


if __name__ == "__main__":
    run_database_app()

