import sqlite3
import streamlit as st
import pandas as pd

import sqlite3
import streamlit as st
import pandas as pd

class DatabaseManager:
    def __init__(self, db_name="FCFS_scheduler_history.db"):
        # store the filename of the database
        self.db_name = db_name
        self.init_db()

    def init_db(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # create table to track each run if not already exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS run_index (
                    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    table_name TEXT,
                    avg_waiting REAL,
                    avg_turnaround REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()


    def save_results(self, df_results: pd.DataFrame,avg_waiting: float,avg_turnaround: float):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute
            # count how many runs already stored in table run_index
            ("SELECT COUNT(*) FROM run_index")
            # gets the next run number
            run_number = cursor.fetchone()[0] + 1
            # update the table name
            table_name = f"table_{run_number}"
            # Saves dataframe results into database as a new table
            df_results.to_sql(table_name, conn, if_exists="replace", index=False)
            cursor.execute
            # insert new row which stores metadata in run_index
            ("INSERT INTO run_index (table_name, avg_waiting, avg_turnaround) VALUES (?,?,?)", (table_name,avg_waiting,avg_turnaround))
            conn.commit()

    def fetch_history(self):
        # null dictionary
        history = {}
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute
            # Retrieve all runs in reverse order to get latest run first
            ("SELECT table_name,avg_waiting, avg_turnaround, timestamp FROM run_index ORDER BY run_id DESC")
            runs = cursor.fetchall()
            # loop through each tuple in runs
            for table_name,avg_waiting, avg_turnaround, timestamp in runs:
                # load results table for each run
                df = pd.read_sql_query
                (f"SELECT * FROM {table_name}", conn)
                # Store data and dataframe results in dictionary
                history[table_name] = (timestamp, avg_waiting, avg_turnaround, df)
        return history


    def clear_history(self):
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT table_name FROM run_index")
            tables = cursor.fetchall()
            # drop all the run tables if they exists
            for (table_name,) in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
            cursor.execute
            # resets the run_index by clearing all data
            ("DELETE FROM run_index")
            conn.commit()

    def export_csv(self, filename="fcfs_history_export.csv"):
        all_data = []
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # retrieves all runs in ascending order
            cursor.execute("SELECT table_name,avg_waiting,avg_turnaround, timestamp FROM run_index ORDER BY run_id")
            runs = cursor.fetchall()
            for table_name,avg_waiting,avg_turnaround, timestamp in runs:
                # loads the run table
                df = pd.read_sql_query(f"SELECT * FROM {table_name}", conn)
                # appends the metadata columns
                df["Average_turnaround_time"] = avg_turnaround
                df["Average_waiting_time"] = avg_waiting
                df["run_timestamp"] = timestamp
                df["run_table"] = table_name
                all_data.append(df)
        # concatenates all runs into one Dataframe
        if all_data:
            final_df = pd.concat(all_data, ignore_index=True)
            # Export to csv format
            final_df.to_csv(filename, index=False)
            return filename
        return None


# Streamlit History Page
def history_page():
    st.set_page_config(page_title="FCFS Database History", layout="wide")
    if st.button("⬅️ Back to Main Menu"):
        st.switch_page("Main_Menu.py")

    st.title("📜 Database History Logs for FCFS Scheduling")
    st.markdown("Review past FCFS scheduling runs here. Each run is saved in a separate table.")

    db_mgr = DatabaseManager()
    # call method fetch_history()
    history = db_mgr.fetch_history()

    if history:
        col1, col2 = st.columns([1, 1])

        with col1:
          # confirmation box to confirm deletion
          confirm_clear = st.checkbox("Confirm clear history?")
          # clear all history button
          if st.button("🗑️ Clear All History", type="secondary"):
           if confirm_clear:
             db_mgr.clear_history()
             st.success("Database history has been cleared.")
             st.rerun()
           else:
             st.warning("Please tick the confirmation box before clearing.")


        if col2.button("📤 Export History to CSV", type="primary"):
            # Generate CSV file for all runs
            filename = db_mgr.export_csv()
            if filename:
                with open(filename, "rb") as f:
                    st.download_button("Download CSV file", f, file_name=filename)
            else:
                st.info("No data to export.")

        # Display each run table
        for table_name, (timestamp, avg_waiting, avg_turnaround, df) in history.items():
            st.write(f" {table_name} — Run at {timestamp}")
            st.metric("Average Waiting Time", f"{avg_waiting:.2f} s")
            st.metric("Average Turnaround Time", f"{avg_turnaround:.2f} s")
            st.dataframe(df, use_container_width=True)
    else:
        st.info("The database is empty. Run FCFS simulation and save results to database.")

if __name__ == "__main__":
   history_page()
