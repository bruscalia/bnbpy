import json
import random
from dataclasses import asdict
from pathlib import Path

from ad_layout import (
    MAX_SEED,
    MIN_SEED,
    RANDOM_SEED,
    InstanceADChain,
    create_ad_edges,
    generate_processing_times_transposed,
    get_m_total,
)

from bnbprob.pafssp.instances import AssemblyFlowShopInstance

# Small-scale mixed assembly/disassembly instances for validating the
# branch-and-bound solver against an exact MIP model. Kept deliberately
# tiny (few jobs, short chain) so the MIP is fast to solve to optimality.
N_JOBS = 10
M_CHAIN = 5
N_INSTANCES = 10


def write_instances_ad_small() -> list[InstanceADChain]:
    rng = random.Random(RANDOM_SEED)
    m_total = get_m_total(create_ad_edges(M_CHAIN))
    instances = list[InstanceADChain]()
    for i in range(1, N_INSTANCES + 1):
        seed = rng.randint(MIN_SEED, MAX_SEED)
        name = f'ad-small-{i:03d}-{N_JOBS}-chain{M_CHAIN}'
        instances.append(
            InstanceADChain(seed, N_JOBS, M_CHAIN, m_total, name)
        )
    with open('instances-ad-small.json', mode='w', encoding='utf8') as f:
        json.dump([asdict(inst) for inst in instances], f, indent=4)
    return instances


def generate_and_save_ad_small() -> None:
    """
    Generate processing times for small mixed assembly/disassembly
    instances and save them to JSON files.
    """
    instances = write_instances_ad_small()
    output_dir = Path('./ad-small')
    output_dir.mkdir(exist_ok=True)
    edges = create_ad_edges(M_CHAIN)
    for instance in instances:
        _, p = generate_processing_times_transposed(
            instance.seed, instance.n_jobs, instance.m_total
        )
        apfsp = AssemblyFlowShopInstance(p, edges)

        output = asdict(apfsp)
        file_path = output_dir / f'{instance.name}.json'
        with open(file_path, mode='w', encoding='utf8') as json_file:
            json.dump(output, json_file, indent=4)
        print(f'Saved {instance.name} to {file_path}')


if __name__ == '__main__':
    generate_and_save_ad_small()
