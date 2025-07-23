from itertools import permutations

def flowShopSolver(processing_time_matrix,order):
    totalJobs = len(order)

    totalMachines = len(processing_time_matrix[0])

    completion_time_matrix = [[0] * totalMachines for _ in range(totalJobs)]

    for j in range(totalJobs):
        for m in range(totalMachines):
            job = order[j]

            if(j == 0):
                if(m == 0):
                    completion_time_matrix[j][m] = processing_time_matrix[job][m]
                else:
                    completion_time_matrix[j][m] = completion_time_matrix[j][m - 1] + processing_time_matrix[job][m]

            if(m == 0):
                completion_time_matrix[j][m] = completion_time_matrix[j - 1][m] + processing_time_matrix[job][m]
            else:
                completion_time_matrix[j][m] = max(completion_time_matrix[j][m-1], completion_time_matrix[j -1][m]) + processing_time_matrix[job][m]


    TFT = sum(completion_time_jobx[-1] for completion_time_jobx in completion_time_matrix)
    Makespan = completion_time_matrix[totalJobs-1][totalMachines-1]
    return [TFT, Makespan]

def NEH(processing_time_matrix,n):
    job_order = list(range(n))#for 5 jobs
    final_job_order = []

    # step1(sort order based on the total processing time for each job)
    sorted_job_order = sorted(job_order, key = lambda x: sum(processing_time_matrix[x]), reverse=True)
    # print(sorted_job_order)

    # step2(Take all possible order of two jobs in the sorted list the with minimum makespan enters the list)
    order1 = [sorted_job_order[0], sorted_job_order[1]]
    order2 = [sorted_job_order[1], sorted_job_order[0]]
    if(flowShopSolver(processing_time_matrix, order1)[1] < flowShopSolver(processing_time_matrix, order2)[1]):
        final_job_order = order1[:]
    else:
        final_job_order = order2[:]

    # step3(Take the restof the jobs one by one insert them in the final_job_order in all possible palces
    # then select the position which incurrs mininmum makespan )
    for j in sorted_job_order[2:]:
        best_pos = -1
        best_order = None
        min_makespan = float('inf')
        for i in range(0,len(final_job_order) + 1):
            testOrder = final_job_order[:i] + [j] + final_job_order[i:]
            x = flowShopSolver(processing_time_matrix,testOrder)[1]
            if(x < min_makespan):
                min_makespan = x
                best_order = testOrder[:]
        final_job_order = best_order[:]
    
    return final_job_order


# Using Nawaz-Enscore-Ham Heuristic based optimization
processing_time_matrix = [[5,3,8,4],
              [6,2,6,3],
              [8,8,4,7],
              [9,3,4,1],
              [6,4,8,3]]
# job0->20
# job1->17
# job2->27
# job3->17
# job4->21

min_tft,min_makespan = flowShopSolver(processing_time_matrix,NEH(processing_time_matrix,5))

print("[tft: ",min_tft,", makepsan: ",min_makespan,"] - for job order",NEH(processing_time_matrix, 5))

