import random


def random_graph(
    size: int, connectivity: float, seed: int | None = None
) -> list[tuple[int, int]]:
    if seed is not None:
        random.seed(seed)
    edges = []
    for i in range(size):
        for j in range(i + 1, size):
            if random.random() < connectivity:
                edges.append((i, j))
    return edges
