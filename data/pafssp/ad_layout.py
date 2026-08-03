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
MIN_CHAIN_LENGTH = 5

# Checkpoints are spaced this many spine nodes apart
CHECKPOINT_STEP = 3
# Minimum gap between checkpoints for a single extra branch to fit
MIN_GAP_FOR_BRANCH = 2


@dataclass
class InstanceADChain:
    seed: int
    n_jobs: int
    m_chain: int
    m_total: int
    name: str


def add_branch(
    edges: list[tuple[int, int]],
    s: int,
    t: int,
    length: int,
    next_node: int,
) -> tuple[int, int]:
    """
    Append a branch of `length` fresh nodes connecting `s` to `t`
    (s -> new nodes -> t).

    Returns
    -------
    next_node : int
        Updated next-free-node id.
    last_node : int
        Id of the last new node (the one merging into `t`), useful for
        attaching further crosslinks onto this branch.
    """
    nodes = list(range(next_node, next_node + length))
    edges.append((s, nodes[0]))
    for a, b in zip(nodes, nodes[1:]):
        edges.append((a, b))
    edges.append((nodes[-1], t))
    return next_node + length, nodes[-1]


def create_ad_edges(m_chain: int) -> list[tuple[int, int]]:
    """
    Create edges for a mixed assembly/disassembly digraph whose longest
    chain has exactly `m_chain` nodes.

    Parameters
    ----------
    m_chain : int
        Number of nodes in the main spine (must be >= MIN_CHAIN_LENGTH)

    Returns
    -------
    edges : list[tuple[int, int]]
        List of directed edges

    Structure:
    - Main spine: 0 -> 1 -> ... -> (m_chain - 1), which alone realizes the
      target longest-chain length.
    - Checkpoints are placed along the spine every CHECKPOINT_STEP nodes,
      starting at node 1 and snapping the last one to the sink
      (m_chain - 1). Between each consecutive checkpoint pair (s, t) with
      gap = t - s, extra branches run in parallel with the spine's own
      s -> ... -> t sub-path:
        - gap >= 3: a 1-node "short" branch and a (gap - 1)-node "long"
          branch (the long one ties the spine sub-path's node count).
        - gap == 2: a single 1-node branch.
      Every interior checkpoint therefore both fans in (from the previous
      window's branches) and fans out (into the next window's branches),
      i.e. it is a genuine assembly+disassembly (AD) machine.
    - A single "semi-line": one long, independently-sourced chain running
      all the way to the sink (ties the spine's total length). Unlike a
      merely-attached extra chain, several of its interior nodes *also*
      fan out into the last node of a checkpoint's long branch (one fork
      per checkpoint that has one, including the sink's own) -- so those
      semi-line nodes become disassembly (D) points bridging the
      semi-line into the core, and the branch nodes they feed become
      assembly (A) points with two independent predecessors, instead of
      the semi-line only ever touching the graph at the final sink.
    """
    if m_chain < MIN_CHAIN_LENGTH:
        raise ValueError(f'm_chain must be at least {MIN_CHAIN_LENGTH}')

    edges = []

    # Main spine: 0 -> 1 -> ... -> (m_chain - 1)
    for i in range(m_chain - 1):
        edges.append((i, i + 1))

    checkpoints = [1]
    while checkpoints[-1] + CHECKPOINT_STEP < m_chain - 1:
        checkpoints.append(checkpoints[-1] + CHECKPOINT_STEP)
    checkpoints.append(m_chain - 1)

    current_node = m_chain
    crosslink_targets = []
    crosslink_nodes = []

    for s, t in zip(checkpoints, checkpoints[1:]):
        gap = t - s
        if gap >= CHECKPOINT_STEP:
            current_node, _ = add_branch(edges, s, t, 1, current_node)
            current_node, last = add_branch(edges, s, t, gap - 1, current_node)
            crosslink_targets.append(t)
            crosslink_nodes.append(last)
        elif gap >= MIN_GAP_FOR_BRANCH:
            current_node, _ = add_branch(edges, s, t, 1, current_node)

    # Semi-line: single independently-sourced chain, ties the spine's
    # length by construction, running all the way to the sink.
    semiline_length = m_chain - 1
    q_nodes = list(range(current_node, current_node + semiline_length))
    for a, b in zip(q_nodes, q_nodes[1:]):
        edges.append((a, b))
    edges.append((q_nodes[-1], m_chain - 1))
    current_node += semiline_length

    # Forks: semi-line node at (1-indexed) position (target - 1) also
    # fans out into that checkpoint's long-branch crosslink node (this
    # applies even when the checkpoint is the sink itself -- the fork
    # lands on the branch's crosslink node, not the sink, so it doesn't
    # duplicate the semi-line's own final edge into the sink). This keeps
    # the longest path exactly m_chain (proof: fork_position (target - 1)
    # + crosslink (1) + checkpoint (1) + remaining spine after checkpoint
    # (m_chain - 1 - target) sums to exactly m_chain).
    for target, crosslink in zip(crosslink_targets, crosslink_nodes):
        fork_node = q_nodes[target - 2]
        edges.append((fork_node, crosslink))

    return edges


def get_m_total(edges: list[tuple[int, int]]) -> int:
    """Get the total number of machines from a list of edges."""
    return max(node for edge in edges for node in edge) + 1


def write_instances_ad_chain() -> list[InstanceADChain]:
    rng = random.Random(RANDOM_SEED)
    instances = list[InstanceADChain]()
    i = 0
    for n_jobs, m_chain in product(N_JOBS, N_CHAINS):
        for _ in range(10):
            i += 1
            seed = rng.randint(MIN_SEED, MAX_SEED)
            m_total = get_m_total(create_ad_edges(m_chain))
            name = f'ad-{i:03d}-{n_jobs}-chain{m_chain}'
            instances.append(
                InstanceADChain(seed, n_jobs, m_chain, m_total, name)
            )
    # Extended instances: 20 jobs, chain length 15 (indices 41-50)
    for _ in range(10):
        i += 1
        seed = rng.randint(MIN_SEED, MAX_SEED)
        m_total = get_m_total(create_ad_edges(15))
        name = f'ad-{i:03d}-20-chain15'
        instances.append(InstanceADChain(seed, 20, 15, m_total, name))
    with open('instances-ad-chain.json', mode='w', encoding='utf8') as f:
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
    output_dir = Path('./ad-chain')
    output_dir.mkdir(exist_ok=True)
    for instance in instances:
        # Generate processing times in transposed format
        _, p = generate_processing_times_transposed(
            instance.seed, instance.n_jobs, instance.m_total
        )
        edges = create_ad_edges(instance.m_chain)
        apfsp = AssemblyFlowShopInstance(p, edges)

        # Save to JSON
        output = asdict(apfsp)
        file_path = output_dir / f'{instance.name}.json'
        with open(file_path, mode='w', encoding='utf8') as json_file:
            json.dump(output, json_file, indent=4)
        print(f'Saved {instance.name} to {file_path}')


if __name__ == '__main__':
    generate_and_save_ad_chain()
