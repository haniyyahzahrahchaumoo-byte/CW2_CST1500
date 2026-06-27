import threading
import time
import streamlit as st
import pandas as pd
import plotly.express as px
from queue import Queue

#Semaphore ensures only one process runs at a time
cpulock = threading.Semaphore(1)

def process_worker(pid,burst, ui_queue):
    '''Simulates the cpu slices'''

    with cpulock:
        # Send live updates to the UI queue
          # Send live updates to the UI queue
        ui_queue.put(("status", f"🟢 Process {pid} is running for {burst}s..."))
        time.sleep(burst)  # Real time delay simulation
        ui_queue.put(("status", f"🔴 Process {pid} paused/finished after {burst}s."))

def round_robin(processes, burst_times, quantum, arrival_times, ui_queue):
    """
    Round Robin CPU Scheduling Algorithm.
    - processes: list of process id (e.g., [1,2,3])
    - burst_times: time the process uses CPU
    - quantum: time slice for each process (default = 2 for all)
    - arrival_times: time at which process arrives (default = 0 for all)
    """

    n = len(processes)

    #Make a copy of burst times so we can reduce them as processes run
    remaining_bt = burst_times[:]
    completion_time = [0] * n
    # clock time is set to 0
    time = 0
    # queue stores process indices
    queue = list(range(n))
    gantt_data = []
    #keeps looping until end of queue
    while queue:
        # takes first process in queue
        i = queue.pop(0)
        start_time = time
        # if process needs more time than quantum
        if remaining_bt[i] > quantum:
            time += quantum
            # calculates remaining burst time after running it for one quantum
            remaining_bt[i] -= quantum
            run_time = quantum
            # simulate process slice
            t = threading.Thread(target=process_worker, args=(processes[i], quantum, ui_queue))
            t.start()
            t.join()
            # Queues again
            queue.append(i)
        #process finishes within quantum
        else:
            # run process for its remaining burst time
            time += remaining_bt[i]
            # record time when process finishes
            run_time = remaining_bt[i]
            remaining_bt[i] = 0
            completion_time[i] = turnaround_time

            # simulate final run
            t = threading.Thread(target=process_worker, args=(processes[i], quantum, ui_queue))
            
            t.start()
            t.join()
            #Track Gantt data
            gantt_data.append(dict(
                Process=f"Process {processes[i]}",
                Start=start_time,
                Finish=time,
                Duration=run_time
            ))
            

    

    # Calculate final performance statistics
    
    turnaround_time = []
    waiting_time = []

    for i in range (n):
     tat = completion_time[i] - arrival_times[i]
     wt= tat - burst_times[i]

     turnaround_time.append(tat)
     waiting_time.append(wt)


    
    df_results = pd.DataFrame({
        "Process": [f"Process {p}" for p in processes],
        "Arrival Time": arrival_times,
        "Burst Time": burst_times,
        "Completion Time(CT)": completion_time,
        "Turnaround Time (TAT = CT - AT)": turnaround_time,
        "Waiting Time(WT = TAT - BT)": waiting_time
    }) 

    # average waiting time
    avg_wt =sum(waiting_time) / n
    # average turnaround time
    avg_tat = sum(turnaround_time) / n
    
    # Send the final payloads back to the Streamlit app thread
    ui_queue.put(('results', (df_results, avg_wt, avg_tat, pd.DataFrame(gantt_data))))
 
    
#  Streamlit UI Configurations
st.set_page_config(page_title="Threaded RR Scheduler", layout="wide")
st.title("🚀Round Robin Scheduler")

# Sidebar Inputs
st.sidebar.header("Configuration")
num_processes = st.sidebar.number_input("Number of Processes", min_value=1, value=1)
quantum = st.sidebar.number_input("Time Quantum (Seconds)", min_value=1, value=2)

burst_times = []
arrival_times = []
processes = list(range(1, num_processes + 1))

for i in processes:
    col1, col2 = st.sidebar.columns(2)
    with col1:
        bt = col2.number_input(f"P{i} Burst (s)", min_value=1, value=3, key=f"bt_{i}")
        burst_times.append(bt)
    with col2:
        at = col1.number_input(f"P{i} Arrival", min_value=0, value=0, key=f"at_{i}")
        arrival_times.append(at)

# Main App Logic 
if st.sidebar.button("Start", type="primary"):
    
    st.subheader("🖥️ Live Thread Execution Logs")
    # A status window container that can update dynamically
    log_container = st.empty()
    log_text = ""
    
    # Thread-safe queue to communicate between background threads and Streamlit
    ui_queue = Queue()
    
    # Run the scheduler loop inside an asynchronous worker thread so it doesn't freeze the main page
    scheduler_thread = threading.Thread(
        target= process_worker, 
        args=(processes, burst_times, quantum, arrival_times, ui_queue)
    )
    scheduler_thread.start()
    
    # Listen to the queue and update Streamlit UI in real-time
    simulation_running = True
    final_data = None
    
    while simulation_running:
        if not ui_queue.empty():
            msg_type, payload = ui_queue.get()
            
            if msg_type == "status":
                log_text += payload + "\n"
                log_container.code(log_text) 
            elif msg_type == "results":
                final_data = payload
                simulation_running = False
        time.sleep(0.1) # Small loop rest to keep CPU usage low
        
    # Post Simulation UI Displays (Metrics, Gantt & DataFrames) 
    st.success("Simulation complete!")
    df_res, avg_wt, avg_tat, df_gantt = final_data
    
    col_m1, col_m2 = st.columns(2)
    col_m1.metric(label="Average Waiting Time", value=f"{avg_wt:.2f} s")
    col_m2.metric(label="Average Turnaround Time", value=f"{avg_tat:.2f} s")
    
    # Draw Gantt Chart
    st.subheader("📊 Gantt Chart Timeline")
    fig = px.timeline(
        df_gantt, 
        x_start=pd.to_datetime(df_gantt['Start'], unit='s'), 
        x_end=pd.to_datetime(df_gantt['Finish'], unit='s'), 
        y="Process", 
        color="Process",
        text="Duration",
        title="Thread Occupancy Chart"
    )
    fig.layout.xaxis.update({'tickformat': '%S', 'title': 'Elapsed Simulation Time (Seconds)'})
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, use_container_width=True)
    
    # Table Summary
    st.subheader("📋 Performance Table")
    st.dataframe(df_res.set_index("Process"), use_container_width=True)