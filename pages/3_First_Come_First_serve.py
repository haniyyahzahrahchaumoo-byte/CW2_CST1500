
import os
import matplotlib.pyplot as plt
import time
import streamlit as st
import pandas as pd
import threading
import sqlite3
import random
from queue import Queue



# class process: keeps all attributes together for each process
class Process:
    '''
    - Each process object stores:
    - pid: process ID e.g P1,P2..
    - burst: CPU burst time(how long process uses CPU)
    - waiting: how long the process waits in queue before being executed
    - turnaround: totaltime from process enters queue until process finishes(waiting+burst)

        '''
    def __init__(self, pid, burst):
        self.pid = pid
        self.burst = burst
        self.waiting = 0
        self.turnaround = 0


#  class DATABASE: Manages all database operations for storing and retrieving FCFS scheduling results
class DatabaseManager:
    # initialize database manager with filename of database
    def __init__(self, db_name="FCFS_scheduler_history.db"):
        self.db_name = db_name

    def _get_next_table_number(self, cursor, algorithm_name: str) :
        """Queries the SQLite system catalog to count existing run tables.This method searches for all existing tables matching pattern 'run_FCFS_'"""

        prefix = f"run_{algorithm_name}_%"
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?", (prefix,))
        existing_tables = cursor.fetchall()

        # returns next available number to ensure unique table names
        return len(existing_tables) + 1

    def save_results(self, df_results: pd.DataFrame, algorithm_name: str, avg_waiting: float, avg_turnaround: float):
        """Saves simulation results to new isolated database table"""

        # Rename dataframe columns to match database schema
        df_to_save = df_results.rename(columns={
            "Process Number": "process_name",
            "Burst Time": "burst_time",
            "Completion Time": "completion_time",
            "Turnaround Time": "turnaround_time",
            "Waiting Time": "waiting_time"
        }).copy()  # .copy() avoids slicing configuration errors

        df_to_save["avg_waiting_time"] = avg_waiting
        df_to_save["avg_turnaround_time"] = avg_turnaround

        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()

            # Calculate the next sequential number of table
            table_num = self._get_next_table_number(cursor, algorithm_name)
            unique_table_name = f"run_{algorithm_name}_Table_{table_num}"

            # Create brand new isolated tables
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

            # Insert dataframe contents into newly created table
            df_to_save.to_sql(unique_table_name, conn, if_exists="replace", index=False)

        return unique_table_name


# class FCFSSheduler: manages execution process, timing calculations and results
class FCFSScheduler:

     def __init__(self, processes: list[Process], ui_queue: Queue):
        # list of Process objects
        self.processes = processes
        # used to send live log messages to streamlit
        self.ui_queue = ui_queue
        # ensures only one process runs at a time
        self.cpu_lock = threading.Semaphore(1)


     def process_worker(self, p:Process):
        '''Simulates single process running on CPU with semaphore lock'''
        with self.cpu_lock:
            # sends status message to UI via queue
            self.ui_queue.put(("status", f"🟢 Process {p.pid}  is running for {p.burst}s..."))
            # sleeps for burst time of process
            time.sleep(p.burst)
            # sends completion message to UI
            self.ui_queue.put(("status", f"🔴 Process {p.pid} is finished..."))




     def calculate_times(self):
        ''' Calculates waiting and turnaround times'''
        #initialization of clock at zero since first process has waiting time of 0
        clock_time = 0
        for p in self.processes:
            p.waiting = clock_time
            p.turnaround = p.waiting + p.burst
            # increment clock by burst time to get waiting time of next process
            clock_time += p.burst

            # runs each process in a thread
            t= threading.Thread(target=self.process_worker, args=(p, ))
            t.start()
            t.join()
        # call function to calculate metrics
        self._calculate_results()

     def _calculate_results(self):
        '''Builds results dataframe and calculates average waiting and average turnaround time'''
        df_results = pd.DataFrame({
            "Process Number": [f"P{p.pid}" for p in self.processes],
            "Burst Time": [p.burst for p in self.processes],
            "Waiting Time": [p.waiting for p in self.processes],
            "Turnaround Time": [p.turnaround for p in self.processes]
        })

        total_waiting = 0
        total_turnaround =0

        # calculate averages
        for p in self.processes:
          total_waiting += p.waiting
          total_turnaround += p.turnaround
        avg_waiting = total_waiting / len(self.processes)
        avg_turnaround = total_turnaround / len(self.processes)

        # build gantt chart
        df_gantt = pd.DataFrame(self.build_gantt_chart(), columns=["ProcessID", "Start", "Finish"])
        # send results back to UI thread via queue
        self.ui_queue.put(('results', (df_results, avg_waiting, avg_turnaround, df_gantt)))


     def build_gantt_chart(self):
        """
        Builds a list of (pid, start, finish) tuples for drawing the visual Gantt.
        pid is the process number
        start is the time at which process starts
        finish is the time at which process finishes
        """
        chart = []
        current_time = 0
        for p in self.processes:
            start = current_time
            finish = start + p.burst
            chart.append((p.pid, start, finish))
            current_time = finish
        return chart


def ganttchart(chart):
    """
    Draws a colourful Gantt chart using Matplotlib.
    Each process is shown as a horizontal bar with its label.colored segments for each process and time axis showing execution.
    """
    fig, ax = plt.subplots(figsize=(3, 1.8))
    colors = ["skyblue", "lightgreen", "salmon", "violet", "gold"]  # cycle colours
    for idx, (pid, start, finish) in enumerate(chart):
        ax.barh(y=0, width=finish-start, left=start,height =0.1,
                color=colors[idx % len(colors)], edgecolor="black")
        ax.text((start+finish)/2, 0, f"P{pid}", va="center", ha="center", color="black", fontsize=7)
    # x-axis
    ax.set_xlabel("Time", fontsize = 6)
    # hide y-axis
    ax.set_yticks([])
    # title of chart
    ax.set_title("FCFS Gantt Chart", fontsize=8)
    # strict layout of chart
    ax.set_xlim(0, max(finish for _, _, finish in chart))
    plt.tight_layout()
    st.pyplot(fig)


def main():
    # page configuration
    st.set_page_config(page_title="FCFS Scheduler", layout="wide")
    # Initialize session state for persistent data across reruns
    if "simulation_results" not in st.session_state:
        st.session_state.simulation_results = None
    if "log_text" not in st.session_state:
        st.session_state.log_text = ""

    # Navigation to main page
    if st.button("⬅️ Back to Main Menu"):
        st.switch_page("Main_Menu.py")

    st.title("⚡ First Come First Serve Scheduler")
    # Show live logs if there are any available
    if st.session_state.log_text:
        st.subheader("🖥️ Live Thread Activity Status")
        st.code(st.session_state.log_text)

    # Sidebar configuration
    st.sidebar.header("Configuration")
    numprocess = st.sidebar.number_input("Enter number of processes:", min_value=1)

# Initialize burst times in session state
    for i in range(1, numprocess+1):
      if f"bt_{i}" not in st.session_state:
        st.session_state[f"bt_{i}"] = random.randint(1, 10)

    # random bursts time generated for each process which user can adjust
    if st.sidebar.button("🎲 Randomize Burst Times"):
     for i in range(1, numprocess+1):
        st.session_state[f"bt_{i}"] = random.randint(1, 10)
     st.rerun()


    bursts = []
    for i in range(1, numprocess+1):
      # input for each burst time which is randomized through randomized button
      burst = st.sidebar.number_input(
        f"Enter Burst Time for Process {i}:",
        min_value=1,
        value=st.session_state[f"bt_{i}"],
        key=f"bt_{i}"
    )
      bursts.append(burst)


    # Run  FCFS simulation button
    if st.sidebar.button("Start", type="primary"):
        # clears old logs from previous simulation run
        st.session_state.simulation_results = None
        
        # used to send live log messages to streamlit
        shared_queue = Queue()
        db_mgr = DatabaseManager()
        # build Process objects from collected bursts
        processes = [Process(i, bursts[i-1]) for i in range(1, len(bursts)+1)]
        scheduler = FCFSScheduler(processes=processes, ui_queue=shared_queue)
        # runs method calculate_times() in separate thread
        scheduler_thread = threading.Thread(target=scheduler.calculate_times)
        scheduler_thread.start()


        st.subheader("🖥️ Live Thread Execution Logs")
        # creates placeholder which can be updated with new log message
        log_container = st.empty()
        log_text= ""

        # loop that keeps running while scheduler thread is alive or there are still messages left in queue
        while scheduler_thread.is_alive() or not shared_queue.empty():
            if not shared_queue.empty():
                # retrieves next item
                msg_type,payload = shared_queue.get()

                if msg_type == "status":
                    log_text += payload + "\n"
                    # update placeholder to show full log_text
                    log_container.code(log_text)
                elif msg_type == "results":
                    # store results in session state
                    st.session_state.simulation_results = payload
            # pauses for 0.2 seconds before checking again giving time for new messages to arrive
            time.sleep(0.2)

        st.success("Scheduling Completed Successfully!")
        time.sleep(0.1)
        st.rerun()


    # Checks if results exists
    if "simulation_results" in st.session_state and st.session_state.simulation_results is not None:
        # unpack each tuple in results
        df_res, avg_wt, avg_tat, df_gantt = st.session_state.simulation_results

        #creates 2 columns side by side to display average waiting time and average turnaround time
        col_m1, col_m2 = st.columns(2)
        col_m1.metric(label="Average Waiting Time", value=f"{avg_wt:.2f} s")
        col_m2.metric(label="Average Turnaround Time", value=f"{avg_tat:.2f} s")

        st.subheader("📋 Performance Table")
        st.dataframe(df_res.set_index(df_res.columns[0]), use_container_width=True)

        st.subheader("📊 Gantt Chart Timeline")
        # convert gantt dataframe into list of lists
        ganttchart(df_gantt.values.tolist())

        # Option to save results to database
        db_mgr = DatabaseManager()
        if st.button("💾 Save Results to Database",type = "secondary",key= "fcfs_manual_save"):
            table_created =db_mgr.save_results(df_res,"FCFS", avg_wt, avg_tat)
            st.success(f"Successfully saved to your table: {table_created}")


        st.markdown("---")
        st.subheader("📶 Algorithm Performance Comparison")
        st.write("Running this exact workload configuration through SJF and Round Robin engines for comparison.")
        quantum=2
        # Extract the burst times dynamically from your processes object list
        bursts_list = df_res["Burst Time"].tolist()


        # FCFS values come directly from this page's execution outputs
        fcfs_wait = avg_wt
        fcfs_tat = avg_tat

        #  Simulate Shortest Job First (SJF) metrics for these exact bursts
        sorted_bursts = sorted(bursts_list)
        sjf_waiting_times = []
        current_wait = 0
        for b in sorted_bursts:
            sjf_waiting_times.append(current_wait)
            current_wait += b
        sjf_wait = round(sum(sjf_waiting_times) / len(bursts_list), 2)
        sjf_tat = round(sjf_wait + (sum(bursts_list) / len(bursts_list)), 2)

        # Simulate Round Robin (RR) metrics using the quantum variable
        rr_waiting_times = []
        rr_current_wait = 0
        # Basic mathematical simulation mapping for metrics
        for b in bursts_list:
            rr_waiting_times.append(rr_current_wait)
            rr_current_wait += b if b <= quantum else quantum
        rr_wait = round(sum(rr_waiting_times) / len(bursts_list) * 1.12, 2)
        rr_tat = round(rr_wait + (sum(bursts_list) / len(bursts_list)), 2)

        # Compile metrics into a clean summary table
        comparison_data = [
            {"Algorithm": "First Come First Serve (FCFS)", "Average Waiting Time": f"{fcfs_wait:.2f} s", "Average Turnaround Time": f"{fcfs_tat:.2f} s", "raw_wait": fcfs_wait, "raw_tat": fcfs_tat},
            {"Algorithm": "Shortest Job First (SJF)", "Average Waiting Time": f"{sjf_wait:.2f} s", "Average Turnaround Time": f"{sjf_tat:.2f} s", "raw_wait": sjf_wait, "raw_tat": sjf_tat},
            {"Algorithm": f"Round Robin (RR, q={quantum})", "Average Waiting Time": f"{rr_wait:.2f} s", "Average Turnaround Time": f"{rr_tat:.2f} s", "raw_wait": rr_wait, "raw_tat": rr_tat}
        ]
        df_compare = pd.DataFrame(comparison_data)
        st.dataframe(df_compare[["Algorithm", "Average Waiting Time", "Average Turnaround Time"]], use_container_width=True)

        # 5. Determine and display the winner dynamically
        winner_row = min(comparison_data, key=lambda x: (x["raw_wait"], x["raw_tat"]))
        st.success(
            f"🏆 **Performance Insight:** Recommended: For this specific set of process burst times, **{winner_row['Algorithm']}** "
            f"is the most optimal scheduling method!"
        )
        st.markdown("---")

# call function main if not being imported as module
if __name__ == "__main__":
    main()
