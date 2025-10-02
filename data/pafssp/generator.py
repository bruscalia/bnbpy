import json
import random
from dataclasses import asdict, dataclass
from itertools import product
from pathlib import Path

from bnbprob.pafssp.instances import (
    AssemblyFlowShopInstance,
    dpm_layout_edges,
    parallel_semilines_edges,
)

# Random definitions
MIN_SEED = 1_000_000_000
MAX_SEED = 10_000_000_000
RANDOM_SEED = 42

# Instance size definitions
N_JOBS = [20, 50]
N_MACHINES_DPM = [(5, 6), (5, 9), (5, 14)]
N_MACHINES_2F = [7, 10, 15]


@dataclass
class InstanceDPm:
    seed: int
    n_jobs: int
    n_first: int
    n_assembly: int
    n_total: int
    name: str


@dataclass
class Instance2Fm:
    seed: int
    n_jobs: int
    n_each: int
    n_total: int
    name: str


def write_instances_dpm() -> list[InstanceDPm]:
    rng = random.Random(RANDOM_SEED)
    instances = list[InstanceDPm]()
    i = 0
    for n_jobs, n_machines_dfm in product(N_JOBS, N_MACHINES_DPM):
        for _ in range(10):
            i += 1
            seed = rng.randint(MIN_SEED, MAX_SEED)
            name = (
                f'dpm-{i:03d}-{n_jobs}-{n_machines_dfm[0]}x{n_machines_dfm[1]}'
            )
            instances.append(
                InstanceDPm(
                    seed,
                    n_jobs,
                    n_machines_dfm[0],
                    n_machines_dfm[1],
                    sum(n_machines_dfm),
                    name,
                )
            )
    with open('instances-dpm.json', mode='w', encoding='utf8') as f:
        json.dump([asdict(inst) for inst in instances], f, indent=4)
    return instances


def write_instances_2f() -> list[Instance2Fm]:
    rng = random.Random(RANDOM_SEED)
    instances = list[Instance2Fm]()
    i = 0
    for n_jobs, n_each in product(N_JOBS, N_MACHINES_2F):
        for _ in range(10):
            i += 1
            seed = rng.randint(MIN_SEED, MAX_SEED)
            name = f'd2f-{i:03d}-{n_jobs}-{n_each}x{n_each}'
            instances.append(
                Instance2Fm(seed, n_jobs, n_each, 2 * n_each - 1, name)
            )
    with open('instances-d2f.json', mode='w', encoding='utf8') as f:
        json.dump([asdict(inst) for inst in instances], f, indent=4)

    return instances


def unif(seed: int, low: int, high: int) -> tuple[int, int]:
    """Replicate Pascal/C uniform random number generator."""
    m = 2147483647
    a = 16807
    b = 127773
    c = 2836
    k = seed // b
    seed = a * (seed % b) - k * c
    if seed < 0:
        seed += m
    value_0_1 = seed / m
    return seed, low + int(value_0_1 * (high - low + 1))


def generate_processing_times_transposed(
    seed: int, num_jobs: int, num_machines: int, low: int = 1, high: int = 99
) -> tuple[int, list[list[int]]]:
    """Generate processing times using Pascal/C random logic."""
    # Transposed: list for each job
    times: list[list[int]] = [[] for _ in range(num_jobs)]
    for _ in range(num_machines):
        for j in range(num_jobs):
            seed, value = unif(seed, low, high)
            times[j].append(value)  # Append to the respective job's list
    return seed, times


def generate_and_save_dpm() -> None:
    """
    Generate processing times for DPM instances and
    save them to JSON files.
    """
    instances = write_instances_dpm()
    output_dir = Path('./dpm')
    output_dir.mkdir(exist_ok=True)
    for instance in instances:
        # Generate processing times in transposed format
        _, p = generate_processing_times_transposed(
            instance.seed, instance.n_jobs, instance.n_total
        )
        edges = dpm_layout_edges(instance.n_first, instance.n_assembly)
        apfsp = AssemblyFlowShopInstance(p, edges)

        # Save to JSON
        output = asdict(apfsp)
        file_path = output_dir / f'{instance.name}.json'
        with open(file_path, mode='w', encoding='utf8') as json_file:
            json.dump(output, json_file, indent=4)
        print(f'Saved {instance.name} to {file_path}')


def generate_and_save_2f() -> None:
    """
    Generate processing times for 2F instances and
    save them to JSON files.
    """
    instances = write_instances_2f()
    output_dir = Path('./d2f')
    output_dir.mkdir(exist_ok=True)
    for instance in instances:
        # Generate processing times in transposed format
        _, p = generate_processing_times_transposed(
            instance.seed, instance.n_jobs, instance.n_total
        )
        edges = parallel_semilines_edges((instance.n_each, instance.n_each))
        apfsp = AssemblyFlowShopInstance(p, edges)

        # Save to JSON
        output = asdict(apfsp)
        file_path = output_dir / f'{instance.name}.json'
        with open(file_path, mode='w', encoding='utf8') as json_file:
            json.dump(output, json_file, indent=4)
        print(f'Saved {instance.name} to {file_path}')


if __name__ == '__main__':
    generate_and_save_dpm()
    generate_and_save_2f()
