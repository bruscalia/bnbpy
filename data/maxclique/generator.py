import json
import os

from bnbprob.maxclique import random_graph

HERE = os.path.dirname(os.path.abspath(__file__))


def main() -> None:
    num_nodes = [50, 100, 200, 300]
    connectivity = [0.3, 0.5, 0.7, 0.9]

    i = 1
    for n in num_nodes:
        for c in connectivity:
            for seed in range(10):
                edges = random_graph(size=n, connectivity=c, seed=seed)
                instance = {
                    'n': n,
                    'connectivity': c,
                    'edges': edges,
                }
                filename = os.path.join(
                    HERE, f'graph_n{n}_{str(i).zfill(3)}.json'
                )
                with open(filename, mode='w', encoding='utf-8') as f:
                    json.dump(instance, f, indent=4)
                i += 1


if __name__ == '__main__':
    main()
