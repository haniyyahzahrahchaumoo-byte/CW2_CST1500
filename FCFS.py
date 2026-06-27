import threading
import time
from tabulate import tabulate
import streamlit as st

#Semaphore ensures only one process runs at a time
cpulock = threading.Semaphore(1)

def get_user_input():
    """
    Asks the user how many processes to schedule and input their respective burst times.
    Returns a list of dictionaries with process number being the key and burst time is the value.

    e.g [ {"Process": 1, "burst": 5},
          {"Process": 2, "burst": 8},
          {"Process": 3, "burst": 12} ]
    """
    print(" \n--- FCFS Scheduler --- ")


    # prompts user to keep entering valid process number
    while True:
        # error handling ensuring only integer values are input
        try:
            # input of number of processors
            process = int(input("How many processes? "))
            # Checking if minimum one process is entered
            if process == 0:
                print("Please enter at least 1 process.")
                continue
            # Checking if process is a negative value
            if process < 0:
                print("Process cannot be negative.")
                continue
            break
        except ValueError:
            print("Invalid input! Please enter integer only.")



    #null list
    processes = []
    # for loop to go through each process and input respective burst time
    for i in range(1, (process + 1)):
        while True:
            try:
                # prompt to enter burst time
                Burst = int(input(f"Enter Burst Time for Process {i}: "))
                # Checks burst time is at least one
                if Burst == 0:
                    print("Burst time must be minimum one.")
                    continue
                # Checks burst time is not negative
                if Burst < 0:
                    print("Burst time cannot be negative.")
                    continue
                # list of dictionaries
                processes.append({"Process":i,"burst":Burst})
                break
            except ValueError:
                print("Invalid input! Please enter integer value .")
    return processes


def build_gantt_chart(processes):
    """
    Builds a list of (pid, start, finish) tuples for drawing the visual Gantt.
    pid is the process number
    start is the time at which process starts
    finish is the time at which process finishes
    """
    chart = []
    current_time = 0
    for p in processes:
        start = current_time
        finish = start + p["burst"]
        chart.append((p["Process"], start, finish))
        current_time = finish
    return chart


def calculatetimes(processes):
    """Calculates waiting time and turnaround time for each process"""
    #initialization of clock at zero since first process has waiting time of 0
    clock_time = 0

    for p in processes:
        # adds new key waiting in list of dictionaries
        # waiting time is how long a process sits in the queue doing nothing
        p["waiting"] = clock_time
        # adds new key turnaround in list of dictionaries
        # turnaround time is the total time from waiting till process is finished ( Waiting Time + Burst Time)
        p["turnaround"] = p["waiting"] + p["burst"]
        # increment clock by the process's burst time in order to get waiting time for next process
        clock_time += p["burst"]
    # updated list with new keys are returned
    return processes


def process_worker(p):
    '''Simulates a process running on CPU.Uses semaphore to ensure FCFS order'''

    with cpulock:
        print(f"Process {p['Process']} is running...")
        # sleeps for burst time of process
        time.sleep(p["burst"])
        print(f"Process {p['Process']} finished.")


def fcfs_scheduling(processes):
    """
    Runs FCFS scheduling with threads and displays results in a table
    """
    # call function to obtain updated list
    processes = calculatetimes(processes)

    # Run each process in FCFS order
    threads = []
    for p in processes:
        # create thread by passing function process worker to thread constructor with argument p
        t = threading.Thread(target=process_worker, args=(p,))
        # appends new thread for each process
        threads.append(t)
        # start thread
        t.start()
        # waits for thread to terminate
        t.join()


    # Results table using tabulate
    table = [[p["Process"], p["burst"], p["waiting"], p["turnaround"]] for p in processes]
    headers = ["Process", "Burst", "Waiting", "Turnaround"]
    print("\n--- FCFS Scheduling Results ---")
    print(tabulate(table, headers=headers, tablefmt="double_grid"))

    #
    # Initialize totals
    total_waiting = 0
    total_turnaround = 0

# Loop through each process and add each waiting and turnaround time respectively
    for p in processes:
        total_waiting += p["waiting"]
        total_turnaround += p["turnaround"]

    # Divide by number of processes to get averages
        avg_waiting = total_waiting / len(processes)
        avg_turnaround = total_turnaround / len(processes)

    print(f"\nAverage Waiting Time: {avg_waiting:.2f}")
    print(f"Average Turnaround Time: {avg_turnaround:.2f}")


    # call function build_gantt_chart
    chart = build_gantt_chart(processes)
    # characters per unit burst time
    unit = 5
    # list holding string segments for the process labels
    labels = []
    timeline = "0"

    for pid, start, finish in chart:
        #calculates width of each process's burst time
        width = (finish - start) * unit
        labels.append("|" + f"P{pid}".center(width))
        # lines up the finish time to the right edge of boundary line
        timeline += " " * (width - len(str(finish)) + 1) + str(finish)
    #joins all label segements into one string
    labels_line = "".join(labels) + "|"

    print("\n--- Gantt Chart ---")
    #output process blocks with the boundary line
    print(labels_line)
    #output time markers aligned under the boundary line
    print(timeline)
    # append results to file
    with open("FCFS.txt", "a", encoding="utf-8") as f:
     f.write(tabulate(table, headers=headers, tablefmt="double_grid"))
     f.write(f"\nAverage Waiting Time: {avg_waiting:.2f}\n")
     f.write(f"Average Turnaround Time: {avg_turnaround:.2f}\n\n")
     f.write(f"Gantt chart\n")
     f.write(labels_line+"\n")
     f.write(timeline)




st.title("FCFS Scheduler")

n = st.number_input("Enter number of processes:", min_value=1, step=1)
bursts = []
for i in range(1, n+1):
    burst = st.number_input(f"Enter Burst Time for Process {i}:", min_value=1, step=1)
    bursts.append(burst)

if st.button("Run FCFS"):
    processes = [{"Process": i+1, "burst": bursts[i]} for i in range(n)]
    table, avg_waiting, avg_turnaround, chart = fcfs_scheduling(processes)

    st.subheader("Results Table")
    st.table(table)

    st.write(f"Average Waiting Time: {avg_waiting:.2f}")
    st.write(f"Average Turnaround Time: {avg_turnaround:.2f}")

    st.subheader("Gantt Chart")
    unit = 5
    labels = []
    timeline = "0"
    for pid, start, finish in chart:
        width = max(1, (finish - start) * unit)
        labels.append("|" + f"P{pid}".center(width))
        timeline += " " * (width - len(str(finish)) + 1) + str(finish)
    labels_line = "".join(labels) + "|"
    st.text(labels_line)
    st.text(timeline)
