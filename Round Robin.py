
from tabulate import tabulate

def round_robin(processes, burst_times, quantum, arrival_times):
    """
    Round Robin CPU Scheduling Algorithm.
    - processes: list of process id (e.g., [1,2,3])
    - burst_times: time the process uses CPU
    - quantum: time slice for each process (default = 2 for all)
    - arrival_times: time at which process arrives (default = 0 for all)
    """

    n = len(processes)


    remaining_bt = burst_times[:]
    completion_time = [0] * n
    # clock time is set to 0
    time = 0
    # queue stores process indices
    queue = list(range(n))

    while queue:
        # take first process in queue
        i = queue.pop(0)
        if remaining_bt[i] > quantum:
            time += quantum
            remaining_bt[i] -= quantum
            queue.append(i)  # put back in queue
        else:
            time += remaining_bt[i]
            remaining_bt[i] = 0
            completion_time[i] = time
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

    avg_wt =totalwaiting / n
    avg_tat = totalturnaound / n

    # Prepare table data
    table = []
    for i in range(n):
        table.append([
            f"{processes[i]}",
            arrival_times[i],
            burst_times[i],
            quantum,
            completion_time[i],
            turnaround_time[i],
            waiting_time[i]
        ])

    columns = ["Process", "Arrival Time", "Burst Time", "Time Quantum",
               "Completion Time", "Turnaround Time", "Waiting Time"]

    print(tabulate(table, headers=columns , tablefmt="grid"))
    print(f"\nAverage Waiting Time for {n} processes is : {avg_wt:.2f}")
    print(f"Average Turnaround Time for {n} processes is : {avg_tat:.2f}")


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
            if process < 1:
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
                if Burst < 1:
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
