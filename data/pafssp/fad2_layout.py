import json
import random
from dataclasses import asdict, dataclass
from itertools import product
from pathlib import Path

from bnbprob.pafssp.instances import AssemblyFlowShopInstance

# Random definitions
MIN_SEED = 1_000_000_000
MAX_SEED = 10_000_000_000
RANDOM_SEED = 12

# Instance size definitions
N_JOBS = [20, 50]
N_CHAINS = [7, 10, 15]
MIN_CHAIN_LENGTH = 2
NUM_PARALLEL = 2


@dataclass
class InstanceADChain:
    seed: int
    n_jobs: int
    m_chain: int
    m_total: int
    name: str


def create_fad_edges(m_chain: int, k: int) -> list[tuple[int, int]]:
    """
    Create edges for a mixed assembly/disassembly digraph whose longest
    chain has exactly `m_chain` nodes.

    Parameters
    ----------
    m_chain : int
        Number of nodes in the main spine (must be >= MIN_CHAIN_LENGTH)

    k : int
        Number of parallel base chains to add. Each machine is connected
        to the next on its chain and the next chain.
        The instances have k source and k sink nodes.

    Returns
    -------
    edges : list[tuple[int, int]]
        List of directed edges
    """
    if m_chain < MIN_CHAIN_LENGTH:
        raise ValueError(f'm_chain must be at least {MIN_CHAIN_LENGTH}')

    result: list[tuple[int, int]] = []
    if m_chain <= 1:
        return result
    for i in range(m_chain - 1):
        for j in range(k):
            mi = i + j * m_chain
            mi_next = mi + 1
            j_next = j + 1
            if j == k - 1:
                j_next = 0
            mj_next = i + j_next * m_chain + 1
            result.append((mi, mi_next))
            result.append((mi, mj_next))

    return result


def get_m_total(m_chain: int, k: int) -> int:
    return m_chain * k


def write_instances_ad_chain() -> list[InstanceADChain]:
    rng = random.Random(RANDOM_SEED)
    instances = list[InstanceADChain]()
    i = 0
    for n_jobs, m_chain in product(N_JOBS, N_CHAINS):
        for _ in range(10):
            i += 1
            seed = rng.randint(MIN_SEED, MAX_SEED)
            m_total = get_m_total(m_chain, NUM_PARALLEL)
            name = f'fa2d-{i:03d}-{n_jobs}-chain{m_chain}'
            instances.append(
                InstanceADChain(seed, n_jobs, m_chain, m_total, name)
            )

    with open('instances-fad2-chain.json', mode='w', encoding='utf8') as f:
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


def generate_and_save_ad_chain() -> None:
    """
    Generate processing times for mixed assembly/disassembly chain
    instances and save them to JSON files.
    """
    instances = write_instances_ad_chain()
    output_dir = Path('./fad2-chain')
    output_dir.mkdir(exist_ok=True)
    for instance in instances:
        # Generate processing times in transposed format
        _, p = generate_processing_times_transposed(
            instance.seed, instance.n_jobs, instance.m_total
        )
        edges = create_fad_edges(instance.m_chain, NUM_PARALLEL)
        apfsp = AssemblyFlowShopInstance(p, edges)

        # Save to JSON
        output = asdict(apfsp)
        file_path = output_dir / f'{instance.name}.json'
        with open(file_path, mode='w', encoding='utf8') as json_file:
            json.dump(output, json_file, indent=4)
        print(f'Saved {instance.name} to {file_path}')


if __name__ == '__main__':
    generate_and_save_ad_chain()
