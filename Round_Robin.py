import threading
import time
import sqlite3
from queue import Queue
import streamlit as st
import pandas as pd
import plotly.express as px


# MODELS & DATA OBJECTS
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
    def __init__(self, db_name="scheduler_history.db"):
        self.db_name = db_name
        
    def save_results(self, df_results: pd.DataFrame):
        """Maps presentation columns to database columns and appends them to SQLite."""
        df_to_save = df_results.rename(columns={
            "Process": "process_name",
            "Arrival Time": "arrival_time",
            "Burst Time": "burst_time",
            "Completion Time(CT)": "completion_time",
            "Turnaround Time (TAT = CT - AT)": "turnaround_time",
            "Waiting Time(WT = TAT - BT)": "waiting_time"
        })
        
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            # Create it right before saving, just in case it's not there
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
        df_to_save.to_sql("simulation_history", conn, if_exists="append", index=False)


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
            self.ui_queue.put(("status", f"🔴 {process.label} paused/finished after {run_time}s."))

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
                Process=proc.label,
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
        df_gantt = pd.DataFrame(self.gantt_data)

        self.ui_queue.put(('results', (df_results, avg_wt, avg_tat, df_gantt)))



# INTERACTION & UI PRESENTATION LAYER
#Handles everything related to layout rendering and application UI state.
st.set_page_config(page_title="RR Scheduler", layout="wide")
st.title("🚀 Round Robin Scheduler")

st.sidebar.header("Configuration")
num_processes = st.sidebar.number_input("Number of Processes", min_value=1, value=1)
quantum = st.sidebar.number_input("Time Quantum (Default=2s)", min_value=1, value=2)

processes = []
for i in range(1, num_processes + 1):
    col1, col2 = st.sidebar.columns(2)
    with col1:
                at = col1.number_input(f"P{i} Arrival", min_value=0, value=0, key=f"at_{i}")
    with col2:
                bt = col2.number_input(f"P{i} Burst (s)", min_value=1, value=3, key=f"bt_{i}")
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

    
     
    st.subheader("🖥️ Live Thread Execution Logs")
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
                db_mgr.save_results(payload[0])   
            time.sleep(0.1)
            
    st.success(" Scheduling Analytics Completed Successfully!")
    st.rerun()
    
# Display current results if they exist
if st.session_state.simulation_results is not None:
    df_res, avg_wt, avg_tat, df_gantt = st.session_state.simulation_results

    col_m1, col_m2 = st.columns(2)
    col_m1.metric(label="Average Waiting Time", value=f"{avg_wt:.2f} s")
    col_m2.metric(label="Average Turnaround Time", value=f"{avg_tat:.2f} s")

    #  Performance Table Summary 
    st.subheader("📋 Performance Table")
    st.dataframe(df_res.set_index("Process"), use_container_width=True)

    #  Drawing Gantt Chart Timeline 
    st.subheader("📊 Gantt Chart Timeline")
    fig = px.timeline(
        df_gantt,
        x_start=pd.to_datetime(df_gantt['Start'], unit='s'),
        x_end=pd.to_datetime(df_gantt['Finish'], unit='s'),
        y="Process",
        color="Process",
        text="Duration"
    )
    fig.layout.xaxis.update({'tickformat': '%S', 'title': 'Time (Seconds)'})
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)

 