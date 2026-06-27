import threading
import time
from tabulate import tabulate

#Semaphore ensures only one process runs at a time
cpulock = threading.Semaphore(1)

def process_worker(pid,burst):
    '''Simulates the cpu slices'''

    with cpulock:
        print(f"Process {pid} is running...")
        # sleeps for burst time of process
        time.sleep(burst)
        print(f"Process {pid} finished.")

def round_robin(processes, burst_times, quantum, arrival_times):
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
    threads = []
    #keeps looping until end of queue
    while queue:
        # takes first process in queue
        i = queue.pop(0)
        # if process needs more time than quantum
        if remaining_bt[i] > quantum:
            time += quantum
            # calculates remaining burst time after running it for one quantum
            remaining_bt[i] -= quantum
            # enqueue process again
            queue.append(i)
            # simulate process slice
            t = threading.Thread(target=process_worker, args=(processes[i], quantum))
            threads.append(t)
            t.start()
            t.join()
        #process finishes within quantum
        else:
            # run process for its remaining burst time
            time += remaining_bt[i]
            # record time when process finishes
            completion_time[i] = time
            # simulate final run
            t = threading.Thread(target=process_worker, args=(processes[i], remaining_bt[i]))
            threads.append(t)
            t.start()
            t.join()
            # mark process as finished
            remaining_bt[i] = 0


    totalturnaound = 0
    totalwaiting = 0

    turnaround_time = []
    waiting_time = []

    for i in range (n):
     tat = completion_time[i] - arrival_times[i]
     wt= tat - burst_times[i]

     turnaround_time.append(tat)
     waiting_time.append(wt)
     totalwaiting += wt
     totalturnaound += tat
    # average waiting time
    avg_wt =totalwaiting / n
    # average turnaround time
    avg_tat = totalturnaound / n

    # Prepare table data
    table = []
    for i in range(n):
        # adds data rowise for each process
        table.append([
            f"{processes[i]}",
            arrival_times[i],
            burst_times[i],
            quantum,
            completion_time[i],
            turnaround_time[i],
            waiting_time[i]
        ])
    # headers of columns inserted
    columns = ["Process", "ArrivalTime", "BurstTime", "TimeQuantum",
               "CompletionTime", "TurnaroundTime", "WaitingTime"]
    # create table with data and headers
    print(tabulate(table, headers=columns , tablefmt="double_grid"))
    print(f"\nAverage Waiting Time for {n} processes is : {avg_wt:.2f}")
    print(f"Average Turnaround Time for {n} processes is : {avg_tat:.2f}")

    # Append the results to file
    with open("RoundRobin.txt", "a", encoding="utf-8") as f:
        f.write("\n--- Round Robin Results ---\n")
        f.write(tabulate(table, headers=columns, tablefmt="fancy_grid")+ "\n")
        f.write(f"Average Waiting Time: {avg_wt:.2f}\n")
        f.write(f"Average Turnaround Time: {avg_tat:.2f}\n\n")

def main():
    """
    Main function to take user input.

    """
#creating null list
processes = []
burst_times = []
arrival_times = []

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


for i in range(1,(process+1)):

            processes.append(i)

            #input of burst time
            while True:
             try:
                # prompt to enter burst time
                Burst = int(input(f"Enter Burst Time for Process {i}: "))
                # Checks burst time is at least one
                if Burst == 0:
                    print(" Burst time must be minimum one.")
                    continue
                # Checks burst time is not negative
                if Burst < 0:
                    print(" Burst time cannot be negative.")
                    continue
                # appends each burst time to list
                burst_times.append(Burst)
                break
             except ValueError:
                print("Invalid input! Please enter integer value.")

            # input of arrival time
            while True:
             try:
                Arrival = int(input(f"Enter Arrival Time for Process {i}(default 0): ") or 0)
                if Arrival < 0:
                    print(" Arrival time cannot be negative.")
                    continue
                arrival_times.append(Arrival)
                break
             except ValueError:
                print("Invalid input! Please enter integer value.")

# input of quantum time
quantum = int(input("Enter Time Quantum(default 2): ") or 2)

#call function with 4 parameters
round_robin(processes, burst_times, quantum, arrival_times)



if __name__ == "__main__":
    main()
