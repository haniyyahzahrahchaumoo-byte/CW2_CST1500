import threading
import time
from tabulate import tabulate
import matplotlib.pyplot as plt
import streamlit as st
import pandas as pd

# Semaphore ensures only one process runs at a time
cpulock = threading.Semaphore(1)

# class process
# keeps all attributes together
class Process:
    '''
    - Each process object stores:
    - pid: process ID e.g P1,P2..
    - burst: CPU burst time
    - waiting: how long the process waits in queue before being executed
    - turnaround: totaltime from process enters queue until process finishes(waiting+burst)

        '''
    def __init__(self, pid, burst):
        self.pid = pid
        self.burst = burst
        self.waiting = 0
        self.turnaround = 0

    def run(self):
        """Simulates a process running on CPU.Uses semaphores to ensure FCFS order"""
        with cpulock:
            print(f"Process {self.pid} is running...")
            # sleeps for burst time of process
            time.sleep(self.burst)
            print(f"Process {self.pid} finished...")

# class FCFSScheduler
# Manages a list of process objects
class FCFSScheduler:
    def __init__(self, processes):
        # ensures at least one process exists
        if not processes:
            raise ValueError("At least one process must be provided.")
        self.processes = processes


    # calculates waiting and turnaround times
    def calculate_times(self):
        #initialization of clock at zero since first process has waiting time of 0
        clock_time = 0
        for p in self.processes:
            p.waiting = clock_time
            p.turnaround = p.waiting + p.burst
            # increment clock by burst time to get waiting time of next process
            clock_time += p.burst


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

    def run(self):
        # call function
        self.calculate_times()

        # Runs each process in FCFS order with threads
        threads = []
        for p in self.processes:
            # create thread
            t = threading.Thread(target=p.run)
            # appends new thread for each process
            threads.append(t)
            # start thread
            t.start()
            # waits for thread to terminate
            t.join()

        # Results table
        table = [[p.pid, p.burst, p.waiting, p.turnaround] for p in self.processes]
        headers = ["Process", "Burst", "Waiting", "Turnaround"]
        results_table = tabulate(table, headers=headers, tablefmt="double_grid")
        df = pd.DataFrame(table, columns=headers)

        print("\n--- FCFS Scheduling Results ---")
        print(results_table)

        total_waiting = 0
        total_turnaround =0
        # Averages
        for p in self.processes:
          total_waiting += p.waiting
          total_turnaround += p.turnaround
        avg_waiting = total_waiting / len(self.processes)
        avg_turnaround = total_turnaround / len(self.processes)

        print(f"\nAverage Waiting Time is: {avg_waiting:.2f}")
        print(f"Average Turnaround Time is: {avg_turnaround:.2f}")

        return df, avg_waiting, avg_turnaround, self.build_gantt_chart()





def ganttchart(chart):
    """
    Draws a colourful Gantt chart using Matplotlib.
    Each process is shown as a horizontal bar with its label.
    """
    fig, ax = plt.subplots(figsize=(6, 2))
    colors = ["skyblue", "lightgreen", "salmon", "violet", "gold"]  # cycle colours
    for idx, (pid, start, finish) in enumerate(chart):
        ax.barh(y=0, width=finish-start, left=start,height =0.3,
                color=colors[idx % len(colors)], edgecolor="black")
        ax.text((start+finish)/2, 0, f"P{pid}", va="center", ha="center", color="black", fontsize=10)
    ax.set_xlabel("Time")
    ax.set_yticks([])  # hide y-axis
    ax.set_title("FCFS Gantt Chart")
    st.pyplot(fig)


# Streamlit
def main():
    st.title("FCFS Scheduler")

    # Step 1: Ask number of processes (error handling via min_value)
    n = st.number_input("Enter number of processes:", min_value=1, step=1)

    # Step 2: Collect burst times interactively
    bursts = []
    for i in range(1, n+1):
        burst = st.number_input(f"Enter Burst Time for Process {i}:", min_value=1, step=1)
        bursts.append(burst)

    # Step 3: Run scheduler when button clicked
    if st.button("Run FCFS"):
        try:
            processes = [Process(i+1, bursts[i]) for i in range(n)]
            scheduler = FCFSScheduler(processes)
            table, avg_waiting, avg_turnaround, chart = scheduler.run()

            # Display results table
            st.subheader("Results Table")
            st.table(table)

            # Display averages
            st.write(f"Average Waiting Time: {avg_waiting:.2f}")
            st.write(f"Average Turnaround Time: {avg_turnaround:.2f}")

            # Display colourful Gantt chart
            st.subheader("Gantt Chart")
            ganttchart(chart)

        except ValueError as e:
            st.error(str(e))

if __name__ == "__main__":
    main()
