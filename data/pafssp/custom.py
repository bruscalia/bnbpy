import json
import random
from dataclasses import asdict, dataclass
from itertools import product
from pathlib import Path

from bnbprob.pafssp.instances import AssemblyFlowShopInstance

# Random definitions
MIN_SEED = 1_000_000_000
MAX_SEED = 10_000_000_000
RANDOM_SEED = 42

# Instance size definitions
N_JOBS = [20, 50]
N_CHAINS = [7, 10]
MIN_CHAIN_LENGTH = 2


@dataclass
class InstanceCustomChain:
    seed: int
    n_jobs: int
    m_chain: int
    m_total: int
    name: str


def create_chain_edges(m_chain: int) -> list[tuple[int, int]]:
    """
    Create edges for a complex digraph with multiple chains merging
    into a main chain.

    Parameters
    ----------
    m_chain : int
        Number of nodes in the main chain (must be >= 2)

    Returns
    -------
    edges : list[tuple[int, int]]
        List of directed edges

    Structure:
    - Main chain: 0 -> 1 -> 2 -> ... -> (m_chain - 1)
    - Second chain: starts at node m_chain, connects to node 1,
      then continues with (m_chain // 2 - 1) more nodes and
      merges at node (m_chain // 2)
    - Third chain: has (m_chain - 1) nodes and merges at
      node (m_chain - 1)
    """
    if m_chain < MIN_CHAIN_LENGTH:
        raise ValueError("m_chain must be at least 2")

    edges = []

    # Main chain: 0 -> 1 -> 2 -> ... -> (m_chain - 1)
    for i in range(m_chain - 1):
        edges.append((i, i + 1))

    current_node = m_chain

    # Second chain: connects to node 1, then merges at position (m_chain // 2)
    merge_pos_2 = m_chain // 2
    chain_2_length = merge_pos_2

    if chain_2_length > 0:
        # First node of chain 2 connects to node 1 of main chain
        edges.append((current_node, 1))
        current_node += 1

        # Create remaining nodes of chain 2
        for _ in range(chain_2_length - 1):
            edges.append((current_node, current_node + 1))
            current_node += 1
        # Connect last node of chain 2 to merge position in main chain
        edges.append((current_node, merge_pos_2))
        current_node += 1

    # Third chain merging at position (m_chain - 1)
    merge_pos_3 = m_chain - 1
    chain_3_length = merge_pos_3

    if chain_3_length > 0:
        # Create third chain nodes
        for _ in range(chain_3_length - 1):
            edges.append((current_node, current_node + 1))
            current_node += 1
        # Connect last node of chain 3 to merge position in main chain
        edges.append((current_node, merge_pos_3))
        current_node += 1

    return edges


def calculate_total_machines(m_chain: int) -> int:
    """Calculate total number of machines for given m_chain."""
    # Main chain: m_chain nodes
    # Second chain: (m_chain // 2) + 1 nodes
    # Third chain: m_chain - 1 nodes
    # Total: m_chain + (m_chain // 2 + 1) + (m_chain - 1)
    #      = 2 * m_chain + m_chain // 2
    return 2 * m_chain + m_chain // 2


def write_instances_custom_chain() -> list[InstanceCustomChain]:
    rng = random.Random(RANDOM_SEED)
    instances = list[InstanceCustomChain]()
    i = 0
    for n_jobs, m_chain in product(N_JOBS, N_CHAINS):
        for _ in range(10):
            i += 1
            seed = rng.randint(MIN_SEED, MAX_SEED)
            m_total = calculate_total_machines(m_chain)
            name = f'custom-{i:03d}-{n_jobs}-chain{m_chain}'
            instances.append(
                InstanceCustomChain(seed, n_jobs, m_chain, m_total, name)
            )
    with open('instances-custom-chain.json', mode='w', encoding='utf8') as f:
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


def generate_and_save_custom_chain() -> None:
    """
    Generate processing times for custom chain instances and
    save them to JSON files.
    """
    instances = write_instances_custom_chain()
    output_dir = Path('./custom-chain')
    output_dir.mkdir(exist_ok=True)
    for instance in instances:
        # Generate processing times in transposed format
        _, p = generate_processing_times_transposed(
            instance.seed, instance.n_jobs, instance.m_total
        )
        edges = create_chain_edges(instance.m_chain)
        apfsp = AssemblyFlowShopInstance(p, edges)

        # Save to JSON
        output = asdict(apfsp)
        file_path = output_dir / f'{instance.name}.json'
        with open(file_path, mode='w', encoding='utf8') as json_file:
            json.dump(output, json_file, indent=4)
        print(f'Saved {instance.name} to {file_path}')


if __name__ == '__main__':
    generate_and_save_custom_chain()
