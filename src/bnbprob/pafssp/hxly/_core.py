# Copyright (c) Hexaly. Permission is hereby granted to use, copy,
# and modify this code for applications developed with Hexaly.
from dataclasses import dataclass

import hexaly.optimizer

from bnbprob.pafssp.instances import AssemblyFlowShopInstance
from bnbprob.pafssp.machinegraph import MachineGraph


@dataclass
class HexalyFlowShop:
    jobs: hexaly.optimizer.HxExpression
    processing_time: list[hexaly.optimizer.HxExpression]
    job_end: list[hexaly.optimizer.HxExpression | None]
    makespan: hexaly.optimizer.HxExpression


@dataclass
class HexalyJobShop:
    jobs: hexaly.optimizer.HxExpression
    tasks: list[list[hexaly.optimizer.HxExpression]]
    makespan: hexaly.optimizer.HxExpression


@dataclass
class HexalyResults:
    permutation: list[int]
    makespan: int


def write_model(
    model: hexaly.optimizer.HxModel,
    instance: AssemblyFlowShopInstance,
) -> HexalyJobShop:
    # Base elements: number of jobs and machines
    nb_jobs = len(instance.p)
    nb_machines = len(instance.p[0])
    # Precedence graph of machines
    graph = MachineGraph.from_edges(instance.edges)

    # Permutation of jobs
    jobs = model.list(nb_jobs)

    # All jobs have to be assigned
    model.constraint(model.eq(model.count(jobs), nb_jobs))

    # Initialize job_end array machine-wise
    M = sum(
        sum(instance.p[j][m] for j in range(nb_jobs))
        for m in range(nb_machines)
    )
    tasks = [
        [model.interval(0, M) for _ in range(nb_machines)]
        for _ in range(nb_jobs)
    ]
    for j in range(nb_jobs):
        for ml in range(nb_machines):
            model.constraint(model.length(tasks[j][ml]) == instance.p[j][ml])

    # Initialize task array
    task_array = model.array(tasks)

    # Precedence constraints on each machine
    for ml in graph.topo_order:
        sequence_lambda = model.lambda_function(
            lambda i: model.lt(
                model.at(task_array, jobs[i], ml),
                model.at(task_array, jobs[i + 1], ml),
            )
        )
        model.constraint(
            model.and_(model.range(0, nb_jobs - 1), sequence_lambda)
        )

    # Precedence constraints for job_end based on the machine graph
    for j in range(nb_jobs):
        for ml in graph.topo_order:
            for mk in graph.prec[ml]:
                model.constraint(tasks[j][mk] < tasks[j][ml])

    # Minimize the makespan: end of the last job on the last machine
    makespan = model.max(
        model.end(tasks[j][ml])
        for ml in graph.rev_topo_order
        for j in range(nb_jobs)
        if not graph.succ[ml]
    )
    model.minimize(makespan)

    model.close()

    return HexalyJobShop(
        jobs=jobs,
        tasks=tasks,
        makespan=makespan,
    )


def solve_hexaly(
    instance: AssemblyFlowShopInstance, time_limit: int = 60
) -> HexalyResults:
    with hexaly.optimizer.HexalyOptimizer() as optimizer:
        model = optimizer.model
        hx_model = write_model(model, instance)
        optimizer.param.time_limit = time_limit
        optimizer.solve()
        makespan = int(hx_model.makespan.value)  # type: ignore
        permutation = [int(j) for j in hx_model.jobs.value]  # type: ignore

    return HexalyResults(
        permutation=permutation,
        makespan=makespan,
    )


def write_model_fs(
    model: hexaly.optimizer.HxModel,
    instance: AssemblyFlowShopInstance,
) -> HexalyFlowShop:
    # Base elements: number of jobs and machines
    nb_jobs = len(instance.p)
    nb_machines = len(instance.p[0])
    # Precedence graph of machines
    graph = MachineGraph.from_edges(instance.edges)

    # Permutation of jobs
    jobs = model.list(nb_jobs)

    # All jobs have to be assigned
    model.constraint(model.eq(model.count(jobs), nb_jobs))

    # For each machine create proccessingTime[m] as an array to be able
    # to access it with an 'at' operator
    processing_time = [
        model.array([instance.p[j][m] for j in range(nb_jobs)])
        for m in range(nb_machines)
    ]

    # Initialize job_end array machine-wise
    job_end: list[hexaly.optimizer.HxExpression | None] = [None] * nb_machines

    # The jth job on machine m starts when it has been processed by
    # all its predecessor machines according to the precedence graph.
    # On the edge case, a machine with no predecessors
    # can start processing immediately, so only the predecessor
    # jobs need to be considered.
    # AND when job j-1 has been processed on machine m.
    # It ends after it has been processed.
    for ml in graph.topo_order:
        end_lambda = model.lambda_function(
            lambda i, prev: model.max(
                prev,
                *(job_end[mk][i] for mk in graph.prec[ml]),  # type: ignore
            )
            + processing_time[ml][jobs[i]]
        )
        job_end[ml] = model.array(model.range(0, nb_jobs), end_lambda, 0)

    # Minimize the makespan: end of the last job on the last machine
    makespan = model.max(
        job_end[ml][nb_jobs - 1]  # type: ignore
        for ml in range(nb_machines)
        if not graph.succ[ml] and job_end[ml] is not None
    )
    model.minimize(makespan)

    model.close()

    return HexalyFlowShop(
        jobs=jobs,
        processing_time=processing_time,
        job_end=job_end,
        makespan=makespan,
    )


# def main(instance_file, output_file, time_limit):
#     nb_jobs, nb_machines, processing_time_data = read_instance(instance_file)

#     with hexaly.optimizer.HexalyOptimizer() as optimizer:
#         #
#         # Declare the optimization model
#         #
#         model = optimizer.model

#         # Permutation of jobs
#         jobs = model.list(nb_jobs)

#         # All jobs have to be assigned
#         model.constraint(model.eq(model.count(jobs), nb_jobs))

#         # For each machine create proccessingTime[m] as an array to be able
#         # to access it with an 'at' operator
#         processing_time = [
#             model.array(processing_time_data[m]) for m in range(nb_machines)
#         ]

#         # On machine 0, the jth job ends on the time it took to be processed
#         # after the end of the previous job
#         job_end = [None] * nb_machines

#         first_end_lambda = model.lambda_function(
#             lambda i, prev: prev + processing_time[0][jobs[i]]
#         )

#         job_end[0] = model.array(model.range(0, nb_jobs), first_end_lambda, 0)

#         # The jth job on machine m starts when it has been processed by machine n-1
#         # AND when job j-1 has been processed on machine m.
#         # It ends after it has been processed.
#         for m in range(1, nb_machines):
#             mL = m
#             end_lambda = model.lambda_function(
#                 lambda i, prev: model.max(prev, job_end[mL - 1][i])
#                 + processing_time[mL][jobs[i]]
#             )
#             job_end[m] = model.array(model.range(0, nb_jobs), end_lambda, 0)

#         # Minimize the makespan: end of the last job on the last machine
#         makespan = job_end[nb_machines - 1][nb_jobs - 1]
#         model.minimize(makespan)

#         model.close()

#         # Parameterize the optimizer
#         optimizer.param.time_limit = time_limit

#         optimizer.solve()

#         #
#         # Write the solution in a file
#         #
#         if output_file is not None:
#             with open(output_file, 'w') as f:
#                 f.write('%d\n' % makespan.value)
#                 for j in jobs.value:
#                     f.write('%d ' % j)
#                 f.write('\n')


# if __name__ == '__main__':
#     if len(sys.argv) < 2:
#         print(
#             'Usage: python flowshop.py instance_file [output_file] [time_limit]'
#         )
#         sys.exit(1)

#     instance_file = sys.argv[1]
#     output_file = sys.argv[2] if len(sys.argv) >= 3 else None
#     time_limit = int(sys.argv[3]) if len(sys.argv) >= 4 else 5
#     main(instance_file, output_file, time_limit)
