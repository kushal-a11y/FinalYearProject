# params:    processing_time_matrix[job][machine]
#            job order[intdex]
# output:    l[TFT, Makespan] 

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

processing_time_matrix = [[5,3,8,4],
              [6,2,6,3],
              [8,8,4,7],
              [9,3,4,1],
              [6,4,8,3]]

# order = [1,4,0,3,2]


# l = flowShopSolver(processing_time_matrix, order)

# print(f"Makespan: {l[1]} || Total Flow Time: {l[0]}")



min_makespan = float('inf')
min_tft = float('inf')
best_permutation = None

for p in permutations(range(5)):
    tft,makespan = flowShopSolver(processing_time_matrix,list(p))
    if(makespan < min_makespan or (makespan == min_makespan and tft<min_tft)):
        min_makespan = makespan
        min_tft = tft
        best_permutation = p

print("[tft: ",min_tft,", makepsan: ",min_makespan,"] - for job order",best_permutation)
