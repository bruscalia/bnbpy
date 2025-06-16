import sys

from ortools.sat.python import cp_model

from bnbprob.pfssp.cp.datamodels import CPFlowShop, CPJob, CPResults


def build_cpsat(p: list[list[int]], lock_perm: bool = True) -> CPFlowShop:
    """Create a constraint programming model using CP-SAT

    Parameters
    ----------
    p : list[list[int]]
        List of processing times for each job

    lock_perm : bool, optional
        Either or not to lock the sequence as a permutation
        (the same for all machines), by default True

    Returns
    -------
    CPFlowShop
        Model instance
    """
    J = len(p)
    M = len(p[0])

    # Create the model
    model = cp_model.CpModel()

    jobs = {j: CPJob(j, p[j]) for j in range(J)}

    # Sets
    V = sum((sum(pi, 0) for pi in p), 0)  # Upper bound on makespan
    machines = list(range(M))

    # Start and end times for each task
    _fill_jobs(model, jobs, machines, V)

    # Makespan variable
    makespan = model.NewIntVar(0, V, 'makespan')

    # Arc variables for the circuit constraint
    if lock_perm:
        arcs = _create_arcs(model, J)

        # Add the circuit constraint
        model.AddCircuit([(i, j, arc) for (i, j), arc in arcs.items()])

        # Add precedence constraints based on the circuit
        for m in machines:
            for (i, j), arc in arcs.items():
                if (i != -1) and (j != -1):
                    model.Add(
                        jobs[j].starts[m] >= jobs[i].ends[m]
                    ).OnlyEnforceIf(arc)

    # Add precedence constraints for each job
    for job in jobs.values():
        for m in machines[:-1]:
            model.Add(job.starts[m + 1] >= job.ends[m])

    # Add disjunctive constraints for all tasks on the same machine
    for m in machines:
        machine_tasks = [job.intervals[m] for job in jobs.values()]
        model.AddNoOverlap(machine_tasks)

    # Objective: Minimize makespan
    for job in jobs.values():
        model.Add(makespan >= job.ends[M - 1])
    model.Minimize(makespan)

    # Create model instance
    flow_model = CPFlowShop(model, jobs, machines, makespan)

    return flow_model


def log_callback(message: str) -> None:
    sys.stdout.write(message + '\n')
    sys.stdout.flush()


def extract_results(
    flow_model: CPFlowShop, solver: cp_model.CpSolver
) -> CPResults:
    result = CPResults(solver.Value(flow_model.makespan), [])
    for job in flow_model.jobs.values():
        job_schedule = []
        for m in flow_model.machines:
            start_time = solver.Value(job.starts[m])
            job_schedule.append(start_time)
        job.r = job_schedule

    sequence = list(flow_model.jobs.values())
    sequence.sort(key=lambda x: x.r[0], reverse=False)
    result.sequence = sequence
    return result


def solve_cpsat(
    flow_model: CPFlowShop, verbose: bool = True, time_limit: int | None = None
) -> CPResults | None:
    # Solve the model
    solver = cp_model.CpSolver()

    if verbose:
        solver.log_callback = log_callback
        solver.parameters.log_search_progress = True

    if time_limit is not None:
        solver.parameters.max_time_in_seconds = time_limit

    status = solver.Solve(flow_model.model)

    # Extract solution
    # Needed to disable ruff due to mypy
    if int(status) in {int(cp_model.OPTIMAL), int(cp_model.FEASIBLE)}:
        return extract_results(flow_model, solver)
    else:
        return None


def _fill_jobs(
    model: cp_model.CpModel,
    jobs: dict[int, CPJob],
    machines: list[int],
    V: int,
) -> None:
    # Start and end times for each task
    for j, job in jobs.items():
        job.starts = []
        job.ends = []
        job.intervals = []
        for m in machines:
            start = model.NewIntVar(0, V, f's_{j}_{m}')
            end = model.NewIntVar(0, V, f'e_{j}_{m}')
            interval = model.NewIntervalVar(
                start, job.p[m], end, f'x_{job}_{m}'
            )
            job.starts.append(start)
            job.ends.append(end)
            job.intervals.append(interval)


def _create_arcs(
    model: cp_model.CpModel, J: int
) -> dict[tuple[int, int], cp_model.IntVar]:
    arcs = {}
    for i in range(J):
        # Dummy arcs make the first position flexible
        from_dummy = model.NewBoolVar(f'arc_dummy_{i}')
        arcs[-1, i] = from_dummy
        to_dummy = model.NewBoolVar(f'arc_{i}_dummy')
        arcs[i, -1] = to_dummy
        for j in range(J):
            if i != j:
                arc = model.NewBoolVar(f'arc_{i}_{j}')
                arcs[i, j] = arc
    return arcs
