import threading
import time
import pandas as pd


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
            process = int(input("\n  How many processes? "))
            # Checking if minimum one process is entered
            if process < 1:
                print("Please enter at least 1 process.")
                continue
            # Checking if process is a negative value
            if process < 0:
                print("Process cannot be negative.")
                continue
            break
        except ValueError:
            print(" Invalid input! Please enter integer only.")



    #null list
    processes = []
    # for loop to go through each process and input respective burst time
    for i in range(1, (process + 1)):
        while True:
            try:
                # prompt to enter burst time
                Burst = int(input(f"  Enter Burst Time for Process {i}: "))
                # Checks burst time is at least one
                if Burst < 1:
                    print(" Burst time must be minimum one.")
                    continue
                # Checks burst time is not negative
                if Burst < 0:
                    print(" Burst time cannot be negative.")
                    continue
                # list of dictionaries
                processes.append({"Process":i,"burst":Burst})
                break
            except ValueError:
                print("Invalid input! Please enter integer value .")
    return processes

# Calculates waiting time and turnaround time for each process
def calculatetimes(processes):
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
        time.sleep(p["burst"])  # simulate CPU burst
        print(f"Process {p['Process']} finished.")


def fcfs_scheduling(processes):
    """
    Runs FCFS scheduling with threads and displays results in a pandas table.
    """
    processes = calculatetimes(processes)

    # Run each process in FCFS order
    threads = []
    for p in processes:
        t = threading.Thread(target=process_worker, args=(p,))
        threads.append(t)
        t.start()
        t.join()  # ensures strict FCFS order

    # Display results in table
    df = pd.DataFrame(processes)
    print("\n--- FCFS Scheduling Results ---")
    print(df.to_string(index=False))

    # Print averages
    avg_waiting = df["waiting"].mean()
    avg_turnaround = df["turnaround"].mean()
    print(f"\nAverage Waiting Time: {avg_waiting:.2f}")
    print(f"\nAverage Turnaround Time: {avg_turnaround:.2f}")


#call function
processes = get_user_input()
fcfs_scheduling(processes)
