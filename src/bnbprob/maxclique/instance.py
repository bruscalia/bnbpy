import random


def random_graph(
    size: int, connectivity: float, seed: int | None = None
) -> list[tuple[int, int]]:
    """Edges of a random graph in which each pair of nodes is connected
    with probability ``connectivity`` (the global random state is not
    modified)."""
    rng = random.Random(seed)
    edges = []
    for i in range(size):
        for j in range(i + 1, size):
            if rng.random() < connectivity:
                edges.append((i, j))
    return edges
