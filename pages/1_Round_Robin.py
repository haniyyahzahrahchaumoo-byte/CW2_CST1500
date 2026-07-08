import threading
import time
import sqlite3
from queue import Queue
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import random
import datetime


# Class process & Data Objects
# keeps all attributes together
class Process:
    """Represents an individual process model and its context tracking."""
    def __init__(self, pid: int, burst_time: int, arrival_time: int = 0):
        self.pid = pid
        self.burst_time = burst_time
        self.arrival_time = arrival_time
        self.remaining_time = burst_time
        self.completion_time = 0
        self.turnaround_time = 0
        self.waiting_time = 0

    @property
    def label(self) :
        return f"Process {self.pid}"



#  DATABASE MANAGEMENT LAYER FOR WRITING RESULTS
class DatabaseManager:
    def __init__(self, db_name="RR_scheduler_history.db"):
        self.db_name = db_name
    def _init_index_table(self, cursor):
        """Initializes a master execution index tracking block."""
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS run_index (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                table_name TEXT,
                avg_waiting REAL,
                avg_turnaround REAL,
                timestamp DATETIME
            )
        """)
    def  _get_next_table_number(self, cursor, algorithm_name: str) -> int:
        """Queries the SQLite system catalog to count existing run tables."""
        # Finds all tables starting with 'run_RR_'
        prefix = f"run_{algorithm_name}_%"
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE ?", (prefix,))
        existing_tables = cursor.fetchall()
        
        
        # Next table number is current count + 1 (Starts at 1 if none exist)
        return len(existing_tables) + 1

    def save_results(self, df_results: pd.DataFrame, algorithm_name: str, avg_waiting: float, avg_turnaround: float):
        """Creates an isolated table sequentially (e.g., run_SJF_Table_1)."""
        
        df_to_save = df_results.rename(columns={
            "Process": "process_name",
            "Arrival Time": "arrival_time",
            "Burst Time": "burst_time",
            "Completion Time(CT)": "completion_time",
            "Turnaround Time (TAT = CT - AT)": "turnaround_time",
            "Turnaround Time (TAT)": "turnaround_time", 
            "Waiting Time(WT = TAT - BT)": "waiting_time",
            
        }).copy() #.copy()avoids slicing configuration errors
        current_now_ts = datetime.datetime.now().isoformat()
        df_to_save["timestamp"] = current_now_ts

        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            self._init_index_table(cursor)

            #Calculate the next sequential number
            table_num = self._get_next_table_number(cursor, algorithm_name)
            unique_table_name = f"run_{algorithm_name}_Table_{table_num}"
            

            # Create brand new isolated tables
            cursor.execute(f"""
                CREATE TABLE IF NOT EXISTS {unique_table_name} 
                (
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
            
            df_to_save.to_sql(unique_table_name, conn, if_exists="append", index=False)
            cursor.execute("INSERT INTO run_index (table_name, avg_waiting, avg_turnaround, timestamp) VALUES (?, ?, ?, ?)",
                (unique_table_name, avg_waiting, avg_turnaround, current_now_ts)
            )
            conn.commit()
        return unique_table_name


#  SCHEDULER & WORKER THREAD LOGIC
class RoundRobinScheduler:
    """Handles the core CPU scheduling algorithm and thread execution."""
    def __init__(self, processes: list[Process], quantum: int, ui_queue: Queue):
        self.processes = processes
        self.quantum = quantum
        self.ui_queue = ui_queue
        self.cpu_lock = threading.Semaphore(1)
        self.gantt_data = []

    def _process_worker(self, process: Process, run_time: int):
        """Simulates CPU burst cycles safely utilizing a Thread Semaphore."""
        with self.cpu_lock:
            self.ui_queue.put(("status", f"🟢 {process.label} is running for {run_time}s..."))
            time.sleep(run_time)
            self.ui_queue.put(("status", f"🔴 {process.label} finished after {run_time}s."))

    def run(self):
        """Executes the Round Robin scheduling simulation loop."""
        n = len(self.processes)
        clock_time = 0
        queue = list(range(n))

        while queue:
            i = queue.pop(0)
            proc = self.processes[i]
            start_time = clock_time

            if proc.remaining_time > self.quantum:
                run_time = self.quantum
                clock_time += run_time
                proc.remaining_time -= run_time
                
                t = threading.Thread(target=self._process_worker, args=(proc, run_time))
                t.start()
                t.join()
                
                queue.append(i)
            else:
                run_time = proc.remaining_time
                clock_time += run_time
                proc.remaining_time = 0
                proc.completion_time = clock_time
                
                t = threading.Thread(target=self._process_worker, args=(proc, run_time))
                t.start()
                t.join()

            self.gantt_data.append(dict(
                ProcessID=proc.pid,
                Start=start_time,
                Finish=clock_time,
                Duration=run_time
            ))

        self._calculate_metrics()

    def _calculate_metrics(self):
        """Computes structural metrics and pipes them to the UI thread."""
        for proc in self.processes:
            proc.turnaround_time = proc.completion_time - proc.arrival_time
            proc.waiting_time = proc.turnaround_time - proc.burst_time

        df_results = pd.DataFrame({
            "Process": [p.label for p in self.processes],
            "Arrival Time": [p.arrival_time for p in self.processes],
            "Burst Time": [p.burst_time for p in self.processes],
            "Completion Time(CT)": [p.completion_time for p in self.processes],
            "Turnaround Time (TAT = CT - AT)": [p.turnaround_time for p in self.processes],
            "Waiting Time(WT = TAT - BT)": [p.waiting_time for p in self.processes]
        })

        avg_wt = sum(p.waiting_time for p in self.processes) / len(self.processes)
        avg_tat = sum(p.turnaround_time for p in self.processes) / len(self.processes)
        df_gantt = pd.DataFrame(self.gantt_data, columns=['ProcessID', 'Start', 'Finish'])

        self.ui_queue.put(('results', (df_results, avg_wt, avg_tat, df_gantt)))
        
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
    Each process is shown as a horizontal bar with its label.
    """
    fig, ax = plt.subplots(figsize=(6,2))
    colors = ["skyblue", "lightgreen", "salmon", "violet", "gold"]  # cycle colours
    for idx, (pid, start, finish) in enumerate(chart):
        ax.barh(y=0, width=finish-start, left=start,height=0.3,
                color=colors[idx % len(colors)], edgecolor="black")
        ax.text((start+finish)/2, 0, f"P{int(pid)}", va="center", ha="center", color="black", fontsize=10)
    ax.set_xlabel("Time(seconds)")
    ax.set_yticks([])  # hide y-axis
    ax.set_title("Round Robin Gantt Chart")
    st.pyplot(fig)



# INTERACTION & UI PRESENTATION LAYER
#Handles everything related to layout rendering and application UI state.
st.set_page_config(page_title="RR Scheduler", layout="wide")
# 🏠 Home navigation button to go back to the Main Menu selection grid
if st.button("⬅️ Back to Main Menu"):
    st.switch_page("Main_Menu.py")
st.title("🔄️ Round Robin Scheduler")


st.sidebar.header("Configuration")
num_processes = st.sidebar.number_input("Number of Processes", min_value=3, value=3)
if "rr_quantum_input" not in st.session_state:
    st.session_state["rr_quantum_input"] = 2

for i in range(1, num_processes + 1):
    if f"ui_at_{i}" not in st.session_state:
        st.session_state[f"ui_at_{i}"] = 0
    if f"ui_bt_{i}" not in st.session_state:
        st.session_state[f"ui_bt_{i}"] = 3

# 2. Add the "Randomize" button (Updates the widget keys directly to avoid silent state freezing)
if st.sidebar.button("🎲 Randomize Inputs & Quantum"):
    st.session_state["rr_quantum_input"] = random.randint(2, 4)
    for i in range(1, num_processes + 1):
        st.session_state[f"ui_at_{i}"] = random.randint(0, 5)
        st.session_state[f"ui_bt_{i}"] = random.randint(1, 10)
    st.rerun()

# 3. Render Quantum input tied to the key directly
quantum = st.sidebar.number_input(
    "Time Quantum (Default=2s)", 
    min_value=2, 
    key="rr_quantum_input"
)

# 4. Render side-by-side inputs using direct key binding
processes = []
for i in range(1, num_processes + 1):
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        at = col1.number_input(
            f"P{i} Arrival", 
            min_value=0, 
            key=f"ui_at_{i}"
        )
    with col2:
        bt = col2.number_input(
            f"P{i} Burst (s)", 
            min_value=1, 
            key=f"ui_bt_{i}"
        )
        
    processes.append(Process(pid=i, burst_time=bt, arrival_time=at))

if "simulation_results" not in st.session_state:
    st.session_state.simulation_results = None

if st.sidebar.button("Start", type="primary"):
    st.session_state.simulation_results = None  
    shared_queue = Queue()
    db_mgr = DatabaseManager()
        
    scheduler = RoundRobinScheduler(
        processes=processes, 
        quantum=quantum, 
        ui_queue=shared_queue
    )
        
    scheduler_thread = threading.Thread(target=scheduler.run)
    scheduler_thread.start()

    
     
    st.subheader("🖥️ Live Thread Activity Status")
    log_container = st.empty()
    log_text = ""
   

    while scheduler_thread.is_alive() or not shared_queue.empty():
         if not shared_queue.empty():
            msg_type, payload = shared_queue.get()   
            if msg_type == "status":
                    log_text += payload + "\n"
                    log_container.code(log_text)
            elif msg_type == "results":
                st.session_state.simulation_results = payload
            time.sleep(0.05)
            
    st.success(" Scheduling Analytics Completed Successfully!")
    time.sleep(0.1)
    st.rerun()
    
# Display current results if they exist
if st.session_state.simulation_results is not None:
    df_res, avg_wt, avg_tat, df_gantt = st.session_state.simulation_results

    col_m1, col_m2 = st.columns(2)
    col_m1.metric(label="Average Waiting Time", value=f"{avg_wt:.2f} s")
    col_m2.metric(label="Average Turnaround Time", value=f"{avg_tat:.2f} s")

    #  Performance Table Summary 
    st.subheader("📋 Performance Table")
    st.dataframe(df_res.set_index(df_res.columns[0]), use_container_width=True)

    save_col1, save_col2 = st.columns([1,3])

    with save_col1:
        if st.button("💾 Save Results to Database", type="secondary", key="rr_manual_save"):
            db_mgr = DatabaseManager(db_name="RR_scheduler_history.db")
            table_created = db_mgr.save_results(df_res, "RR", avg_wt, avg_tat )
            st.success(f"Successfully saved to your table: {table_created}")

    #  Drawing Gantt Chart Timeline 
    st.subheader("📊 Gantt Chart Timeline")
    ganttchart(df_gantt.values.tolist())

    st.markdown("---")
    st.subheader("📶 Algorithm Performance Comparison")
    st.write("Running this exact workload configuration through FCFS and SJF engines for comparison.")

    bursts_list = [p.burst_time for p in processes]

    # 1. Round Robin values come from this page's variables
    rr_wait = avg_wt
    rr_tat = avg_tat

    # 2. Simulate FCFS metrics for these bursts
    fcfs_waiting_times = []
    current_wait = 0
    for b in bursts_list:
        fcfs_waiting_times.append(current_wait)
        current_wait += b
        fcfs_wait = round(sum(fcfs_waiting_times) / len(bursts_list), 2)
    fcfs_tat = round(fcfs_wait + (sum(bursts_list) / len(bursts_list)), 2)

    # 3. Simulate Shortest Job First (SJF) metrics for these bursts
    sorted_bursts = sorted(bursts_list)
    sjf_waiting_times = []
    current_wait = 0
    for b in sorted_bursts:
        sjf_waiting_times.append(current_wait)
        current_wait += b
    sjf_wait = round(sum(sjf_waiting_times) / len(bursts_list), 2)
    sjf_tat = round(sjf_wait + (sum(bursts_list) / len(bursts_list)), 2)

        # 4. Compile metrics into a clean summary table
    comparison_data = [
            {"Algorithm": "First Come First Serve (FCFS)", "Average Waiting Time": f"{fcfs_wait:.2f} s", "Average Turnaround Time": f"{fcfs_tat:.2f} s", "raw_wait": fcfs_wait, "raw_tat": fcfs_tat},
            {"Algorithm": "Shortest Job First (SJF)", "Average Waiting Time": f"{sjf_wait:.2f} s", "Average Turnaround Time": f"{sjf_tat:.2f} s", "raw_wait": sjf_wait, "raw_tat": sjf_tat},
            {"Algorithm": f"Round Robin (RR, q={st.session_state.get('time_quantum', 2)})", "Average Waiting Time": f"{rr_wait:.2f} s", "Average Turnaround Time": f"{rr_tat:.2f} s", "raw_wait": rr_wait, "raw_tat": rr_tat}
        ]
    df_compare = pd.DataFrame(comparison_data)
    st.dataframe(df_compare[["Algorithm", "Average Waiting Time", "Average Turnaround Time"]], use_container_width=True)

      # Determine and display the winner dynamically
    winner_row = min(comparison_data, key=lambda x: (x["raw_wait"], x["raw_tat"]))
    st.success(
            f"🏆 **Performance Insight:** Recommended: For this specific set of process burst times, **{winner_row['Algorithm']}** "
            f"is the most optimal scheduling method!"
        )
    st.markdown("---")


 