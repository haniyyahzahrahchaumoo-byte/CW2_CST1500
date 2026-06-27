import threading
import pandas as pd
import streamlit as st
import time

# Setting up the Streamlit Page Configuration
st.set_page_config(page_title= 'Shortest Job First(SJF) Scheduling Simulator',layout = 'wide')


def get_positive_int(prompt):
    """
    Helper function to guarantee a valid, positive integer input.
    Repeatedly prompts the user until they provide an integer greater than zero.
    """
    while True:
        try:
            # Attempt to convert user input into an integer
            value = int(input(prompt))
            
            # Check if the number is positive (scheduling metrics require > 0 values)
            if value <= 0:
                print("Input must be greater than zero. Please try again.")
                continue  # Restart the loop to ask again
                
            return value  # Return valid input and exit the function
            
        except ValueError:
            # Handle cases where input cannot be parsed as an integer (e.g., letters, floats)
            print("Invalid input. Please enter a valid whole number.")

def run_sjf():
    print("\n--- Shortest Job First (SJF) Non-Preemptive ---")
    
    # List to hold process dictionaries, e.g., [{"id": 1, "burst": 5}]
    job_list = []
    
    try:
        
        num_processes = get_positive_int("Enter number of processes(Press Cltr+C to cancel): ")
        
        # Collect burst time for each individual process
        for i in range(num_processes):
            bt = get_positive_int(f"Enter burst time for Process {i+1}: ")
            job_list.append({"id": i + 1, "burst": bt})      

    except (KeyboardInterrupt, SystemExit):
        # This handles Ctrl+C or early termination signals
        print("\n\nOperation cancelled by user.")
        return
    
    # Guard clause in case the process collection loop was empty or bypassed
    if not job_list:
        print("No processes entered. Exiting.")
        return

  
    # Sorting the list in ascending order ensures the CPU processes them in the optimal sequence.
    job_list.sort(key=lambda x: x["burst"])

    # Initialize tracking structures based on the total number of processes
    n = len(job_list)

  
    results      = {}       # { process_id: { burst, waiting_time, turnaround_time } }
    current_time = [0]      # Wrapped in a list so threads can mutate it

    # Lock — protects current_time and results from simultaneous writes
    results_lock = threading.Lock()

    # Binary semaphore (value=1)
    # Only one thread may hold it at a time, enforcing non-preemptive execution.
    cpu_semaphore = threading.Semaphore(1)

    # Barrier — all n threads must reach this point before any one of them
    # is allowed to compete for the CPU. Prevents early-spawned threads from
    # finishing before later ones are even created, which would corrupt the
    # simulated arrival order.
    barrier = threading.Barrier(n)

    #  Per-process thread function 
    def process_task(index):
        """
        Simulates one process:
          1. Wait at the barrier until every thread is ready.
          2. Acquire the semaphore (queue for the CPU).
          3. Record timing, sleep to simulate work, release the semaphore.
        """
        proc = job_list[index]
        barrier.wait()
        cpu_semaphore.acquire()

        try:
    
            with results_lock:
                # All processes assumed to arrive at time 0, so:
                #   waiting_time    = current_time (time spent in the ready queue)
                #   turnaround_time = waiting_time + burst_time
                wt  = current_time[0]
                tat = wt + proc["burst"]
                current_time[0] += proc["burst"]   # Advance the simulated clock

            # Simulate CPU execution — sleep proportional to burst time
            time.sleep(proc["burst"] * 0.1)

            with results_lock:
                results[proc["id"]] = {
                    "burst"          : proc["burst"],
                    "waiting_time"   : wt,
                    "turnaround_time": tat,
                }

            print(f"  [Thread-{index}] P{proc['id']} done  |  "
                  f"Burst={proc['burst']}  WT={wt}  TAT={tat}")

        finally:
            
            cpu_semaphore.release()

    #  Spawn one thread per process 
    threads = [
        threading.Thread(target=process_task, args=(i,), name=f"P{job_list[i]['id']}")
        for i in range(n)
    ]

    print("\n[ All threads spawned and queued]\n")

    for t in threads:
        t.start()

    # Main thread blocks here until every worker thread has finished
    for t in threads:
        t.join()

    print("\n[All threads completed]\n")

    # Tabulate results rows and compute averages for waiting and turnaround times
    table_rows   = []
    waiting_times     = []
    turnaround_times  = []

    for job in job_list:
        r = results[job["id"]]
        table_rows.append([
            f"P{job['id']}",
            r["burst"],
            r["waiting_time"],
            r["turnaround_time"],
        ])
        waiting_times.append(r["waiting_time"])
        turnaround_times.append(r["turnaround_time"])

    avg_wt  = sum(waiting_times)    / n
    avg_tat = sum(turnaround_times) / n

    # tabulate output 
    headers = ["Process", "Burst Time", "Waiting Time", "Turnaround Time"]

    print(tabulate(table_rows, headers=headers, tablefmt="double_grid"))

    # Output the table for summary of average waiting time and average turnaround time
    summary_rows = [
        ["Average Waiting Time", f"{avg_wt:.2f}"],
        ["Average Turnaround Time", f"{avg_tat:.2f}"],
    ]
    print(tabulate(summary_rows, tablefmt="double_grid"))

# Call the function
run_sjf() 