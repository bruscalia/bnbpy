def load_instance(filename: str):
    with open(filename, mode='r', encoding='utf8') as file:
        lines = file.readlines()
        header = lines[0].strip().split()
        n_nodes = int(header[2])
        edges = []
        node_set = set()
        for line in lines[1:]:
            if line.startswith('e'):
                _, i, j = line.strip().split()
                edges.append((int(i), int(j)))
                node_set.add(int(i))
                node_set.add(int(j))
    nodes = sorted(node_set)
    assert len(nodes) == n_nodes, 'Wrong number of nodes specified'
    return {'nodes': nodes, 'edges': edges}


def load_instance_alt(filename: str):
    with open(filename, mode='r', encoding='utf8') as file:
        lines = file.readlines()
        header = lines[0].strip().split()
        n_nodes = int(header[2])
        edges = []
        node_set = set()
        for line in lines[1:]:
            if line.startswith('e'):
                _, i, j = line.strip().split()
                i, j = (int(i) - 1, int(j) - 1)
                edges.append((int(i), int(j)))
                node_set.add(int(i))
                node_set.add(int(j))
    nodes = sorted(node_set)
    assert len(nodes) == n_nodes, 'Wrong number of nodes specified'
    return {'nodes': nodes, 'edges': edges}


def rewrite_file(filename: str):
    with open(filename, mode='r', encoding='utf8') as f:
        t = f.readlines()
    t_alt = [t[0]] + [f'e {t[i]}' for i in range(1, len(t))]
    with open(filename, mode='w', encoding='utf8') as f:
        for line in t_alt:
            f.write(line)


def rewrite_file_alt(filename: str):
    with open(filename, mode='r', encoding='utf8') as f:
        t = f.readlines()
    t_alt = [t[0]] + [f'e {t[i]}' for i in range(1, len(t))]
    with open(filename, mode='w', encoding='utf8') as f:
        for line in t_alt:
            f.write(line)
