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
            # Store metadata using a 1-based index for user-friendly IDs
            job_list.append({"id": i + 1, "burst": bt})
            
    except (KeyboardInterrupt, SystemExit):
        # This handles Ctrl+C or early termination signals
        print("\n\nOperation cancelled by user.")
        return
    
    # Guard clause in case the process collection loop was empty or bypassed
    if not job_list:
        print("No processes entered. Exiting.")
        return

  
    # SJF prioritizes the shortest jobs first. Sorting the list in ascending 
    # order ensures the CPU processes them in the optimal sequence.
    job_list.sort(key=lambda x: x["burst"])

    # Initialize tracking structures based on the total number of processes
    n = len(job_list)
    waiting_time = [0] * n      # Time each process waits in the ready queue
    turnaround_time = [0] * n  # Total time from arrival to completion

    
    # The very first job in the sorted list starts immediately, so waiting time is 0.
    waiting_time[0] = 0
    
    # Waiting time for current process = (Waiting time of previous process) + (Burst time of previous process)
    for i in range(1, n):
        waiting_time[i] = waiting_time[i - 1] + job_list[i - 1]["burst"]

    # Calculate Turnaround Time for all processes.
    # Turnaround Time = Burst Time + Waiting Time (since Arrival Time is 0)
    for i in range(n):
        turnaround_time[i] = job_list[i]["burst"] + waiting_time[i]

    avg_wt = sum(waiting_time) / n
    avg_tat = sum(turnaround_time) / n

    #Display Output table
    print("\n" + "=" * 55)
    # Formatted column headers with left alignment (<) and static widths
    print(f"{'Process':<10}{'Burst Time':<15}{'Waiting Time':<15}{'Turnaround Time':<15}")
    print("=" * 55)
    
    # Print the specific metrics gathered for each sorted process
    for i in range(n):
        proc_label = f"P{job_list[i]['id']}"
        print(f"{proc_label:<10}{job_list[i]['burst']:<15}{waiting_time[i]:<15}{turnaround_time[i]:<15}")
        
    # Print summary performance metrics
    print("-" * 55)
    print(f"Average Waiting Time:     {avg_wt:.2f}")
    print(f"Average Turn Around Time: {avg_tat:.2f}")
    print("=" * 55)

# Call the function
run_sjf()