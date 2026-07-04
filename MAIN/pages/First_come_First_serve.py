import matplotlib.pyplot as plt
import time
import streamlit as st
import pandas as pd
import threading
import sqlite3
import random
from queue import Queue
from CW2_CST1500.MAIN.pages.FCFS_Database import DatabaseManager



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
        '''Simulates process running in fcfs order'''
        with self.cpu_lock:
            self.ui_queue.put((f"🟢 Process {p.pid}  is running for {p.burst}s..."))
            # sleeps for burst time of process
            time.sleep(p.burst)
            self.ui_queue.put(( f"🔴 Process {p.pid} is finished..."))




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
            t.start(); t.join()
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
        # send results back to streamlit
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
    Each process is shown as a horizontal bar with its label.
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
    st.set_page_config(page_title="FCFS Scheduler", layout="wide")
    # Initialize session state
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
        st.subheader("🖥️ Live Thread Execution Logs")
        st.code(st.session_state.log_text)

    # Sidebar configuration
    st.sidebar.header("Configuration")
    numprocess = st.sidebar.number_input("Enter number of processes:", min_value=1)



    # random bursts time generated for each process which user can adjust
    bursts = []
    for i in range(1, numprocess+1):
        random_burst = random.randint(1, 10)
        burst = st.sidebar.number_input(f"Enter Burst Time for Process {i}:", min_value=1, value=random_burst, key=f"bt_{i}")
        bursts.append(burst)

    # Run  FCFS simulation button
    if st.sidebar.button("Simulate FCFS", type="primary"):
        # clears old logs from previous simulation run
        st.session_state.log_text = ""
        # ensures simulations     starts fresh
        st.session_state.simulation_results = None

        processes = [Process(i+1, bursts[i]) for i in range(numprocess)]
        # used to send live log messages to streamlit
        shared_queue = Queue()
        scheduler = FCFSScheduler(processes=processes,
         ui_queue=shared_queue)
        # runs method calculate_times() in seperate threads
        scheduler_thread = threading.Thread(target=scheduler.calculate_times)
        scheduler_thread.start()


        st.subheader("🖥️ Live Thread Execution Logs")
        # creates placeholder which can be updated with new log message
        log_container = st.empty()


        # loop that keeps running while scheduler thread is alive or there are still messages left in queue
        while scheduler_thread.is_alive() or not shared_queue.empty():
            if not shared_queue.empty():
                # retrieves next item
                payload = shared_queue.get()

                if isinstance(payload, str):
                    # append the string to log_text in session state
                    st.session_state.log_text += payload + "\n"
                    # update placeholder to show full log_text
                    log_container.code(st.session_state.log_text)
                elif isinstance(payload, tuple) and payload[0] == "results":
                    # store results in session state
                    st.session_state.simulation_results = payload[1]
            # pauses for 0.2 seconds before checking again giving time for new messages to arrive
            time.sleep(0.2)

        st.success("Scheduling Completed Successfully!")


    # Checks if results exists
    if "simulation_results" in st.session_state and st.session_state.simulation_results is not None:
        # unpack each tuple in results
        df_res, avg_wt, avg_tat, df_gantt = st.session_state.simulation_results

        #crates 2 columns side by side to display average waiting time and average turnaround time
        col_m1, col_m2 = st.columns(2)
        col_m1.metric(label="Average Waiting Time", value=f"{avg_wt:.2f} s")
        col_m2.metric(label="Average Turnaround Time", value=f"{avg_tat:.2f} s")

        st.subheader("📋 Performance Table")
        st.dataframe(df_res.set_index("Process Number"), use_container_width=True)

        st.subheader("📊 Gantt Chart Timeline")
        # convert gantt dataframe into list of lists
        ganttchart(df_gantt.values.tolist())

        # Option to save results to database
        db_mgr = DatabaseManager()
        if st.button("💾 Save Results to Database"):
            db_mgr.save_results(df_res,avg_wt, avg_tat)
            st.success("Results saved to database.")

# call function main if not being imported as module
if __name__ == "__main__":
    main()
