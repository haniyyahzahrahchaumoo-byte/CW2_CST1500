import sqlite3
import streamlit as st
import pandas as pd

# Database Management & Logic Layer(OOP)
class SJFDatabaseViewer:
    def __init__(self, db_name="sjf_scheduler_history.db"):
        #Store the database filename as an instance attribute
        self.db_name = db_name

    def get_all_run_tables(self) -> list:
        """Queries the database schema to locate all isolated SJF tables."""
        try:
            with sqlite3.connect(self.db_name) as conn:
                cursor = conn.cursor()

                #Query SQLite's internal schema table for matching table names
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'run_SJF_Table_%'")
                # Unpack list of single-value tuples into a plain list of strings
                tables = [row[0] for row in cursor.fetchall()]
                
                # Sort them numerically descending so the newest run is first
                tables.sort(key=lambda x: int(x.split("_")[-1]), reverse=True)
                return tables
        except Exception as e:
            # Handle connection errors gracefully
            st.error(f"Database extraction connection error: {e}")
            return []

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
            conn.commit() # Persist the changes

    def export_csv_data(self, all_tables: list) -> str:
        """Combines all isolated tables into a single CSV string formatted for downloading."""
        all_data = []
        with sqlite3.connect(self.db_name) as conn:
            for table in all_tables:
                df = pd.read_sql_query(f"SELECT * FROM {table}", conn)
                run_num = table.split('_')[-1]
                # Tag each row with its run number
                df["run_table"] = table
                df["run_index_number"] = f"Run #{run_num}"
                if "timestamp" in df.columns:
                    df["run_timestamp"] = df["timestamp"]
                
                all_data.append(df)
                
        if all_data:
            # Stack all run Dataframes into one combined table
            final_df = pd.concat(all_data, ignore_index=True)

            # Remove internal/duplicate columns not needed in the export
            final_df = final_df.drop(columns=["id", "timestamp"], errors="ignore")
            return final_df.to_csv(index=False)
        return ""


#  Interaction & Presentation layer
def run_database_app():

    st.set_page_config(page_title="SJF Database History", layout="wide")
    
    # Navigation back to the Main menu page
    if st.button("⬅️ Back to Main Menu"):
        st.switch_page("Main_Menu.py")

    st.title("🗄️ Shortest Job First Scheduling Process History")
    st.markdown("Inspect performance analytics across individual or multiple simulation runs.")

    # Create the database handler object and fetch available run tables
    viewer = SJFDatabaseViewer()
    tables = viewer.get_all_run_tables()

    # Database Management Action UI Element
    # Stop early if there is no data to show
    st.markdown("### ⚙️ Database Management")
    if not tables:
        st.info("ℹ️ No results found. Run a simulation and save the results first!")
        return  

    # Button to clear all stored history
    if st.button("🗑️ Clear All SJF History", type="primary", key="clear_sjf"):
        viewer.delete_all_history(tables)
        st.success("🎉 All Shortest Job First history tables cleared successfully!")
        st.rerun() # Refresh the page so the cleared state is reflected
    # Export all history as a downloadable CSV
    csv_data = viewer.export_csv_data(tables)
    if csv_data:
        st.download_button(
            label="📤 Export All History to CSV",
            data=csv_data,
            file_name="sjf_history_export.csv",
            mime="text/csv",
            type="primary"
        )
    st.markdown("---")

    # Build the choices dropdown, with an "ALL" option listed first
    options_list = ["ALL_RUNS"] + tables
    display_options = {t: f"🏆 Simulation Run #{t.split('_')[-1]}" for t in tables}
    display_options["ALL_RUNS"] = "📊 Show All Tables"
    
    selected_table_raw = st.selectbox(
        "🔍 Select a Simulation Run to Inspect:",
        options=options_list,
        format_func=lambda x: display_options[x] #Show display-friendly labels only
    )
    
    st.markdown("---")
    
    # Display logic
    if selected_table_raw == "ALL_RUNS":
        st.subheader("📊 All Simulation Runs")
        
        # Loop through each table and render them one by one, keeping them unmerged
        for table in tables:
            run_num = table.split('_')[-1]
            df_raw = viewer.fetch_table_data(table)
            
            st.markdown(f"### Table {run_num}")
            if "timestamp" in df_raw.columns:
                st.caption(f"📅 **Execution Date & Time:** {df_raw['timestamp'].iloc[0]}")
            
            # Hide internal columns not meant for end-user viewing
            df_clean = df_raw.drop(columns=["id", "timestamp"], errors="ignore")
            st.dataframe(df_clean, use_container_width=True)
            st.markdown("---") # Visual divider between the tables
            
    else:
        # Display just the single chosen table
        run_num = selected_table_raw.split('_')[-1]
        df_raw = viewer.fetch_table_data(selected_table_raw)
        
        st.subheader(f"📋 Results for Run {run_num}")
        if "timestamp" in df_raw.columns:
            st.caption(f"📅 **Execution Date & Time:** {df_raw['timestamp'].iloc[0]}")
            
        df_clean = df_raw.drop(columns=["id", "timestamp"], errors="ignore")
        st.dataframe(df_clean, use_container_width=True)

# Ensures the app only runs when this file is executed directly
if __name__ == "__main__":
    run_database_app()