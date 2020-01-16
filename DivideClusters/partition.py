import numpy as np


def partition(graph, max_paper_per_reviewer=10, min_reviewer_per_paper=3,
              ban_set=None, divide_method='even'):
    """
    Partiion the conflict graph into two sets of reviewers and papers. 
    By default choose the most even partition.
    :param graph: Adjancy matrix of the binary conflict graph.
    :type: numpy matrix n*m, g[i][j]=1 means reviewer i has conflict with paper j
    :param max_paper_per_reviewer: Maximum number of papers that a reviewer gets
    :type: Integer
    :param min_reviewer_per_paper: Minimum number of papers that a paper gets
    :type: Integer
    :param ban_set: banned set of reviewers and papers. i for ith reviewer, -j for jth paper.
    :type: set() 
    :default: None (empty set)
    :param divide_method: Method to partition. 
    'even' (default): look for most even partion. 
    'workload': look for most balanced work load.
    'random': Randomly divide, ignore the graph.
    :type: str
    Return: two tuples (R1,P1) and (R2,P2). R1,P1 are lists containing the reviewers and
    papers in partition 1, and R2,P2 for partition 2.
    """
    if divide_method == 'random':
        num_authors, num_papers = graph.shape
        comp1_a = np.random.choice(num_authors, num_authors // 2, replace = False)
        comp1_p = np.random.choice(num_papers, num_papers // 2, replace = False)
        solution_best = (comp1_a, comp1_p)
        solution_another = ([i for i in range(num_authors) if i not in solution_best[0]],
                        [j for j in range(num_papers) if j not in solution_best[1]])  
        return solution_best, solution_another      


    if ban_set is None:
        ban_set = set()
    num_authors, num_papers = graph.shape
    authors = [i for i in range(num_authors)]
    papers = [-i for i in range(num_papers)]
    nodes = {node: [] for node in authors + papers}
    for i in range(num_authors):
        for j in range(num_papers):
            if graph[i][j]:
                nodes[i].append(-j)
                nodes[-j].append(i)

    components = BFS(authors, papers, nodes, ban_set)
    components = sorted(components, key=lambda x: (len(x[0]), len(x[1])))
    number_components, author_sizes, paper_sizes = statistics(components)
    #     pdb.set_trace()
    print("Number of components:", number_components)
    print("Number of authors in connected components:", author_sizes)
    print("Number of papers in connected components:", paper_sizes)
    author_cumsum = np.cumsum(author_sizes)
    paper_cumsum = np.cumsum(paper_sizes)
    # compute knapsack
    n_components = len(components)
    T = np.zeros((n_components, num_authors + 1, num_papers + 1), dtype=int)
    T[0, 0, 0] = 1
    T[0, len(components[0][0]), len(components[0][1])] = 1
    for c in range(1, n_components):
        T[c, 0, 0] = 1
        if c % 10 == 0:
            print('component', c)
        for i in range(author_cumsum[c] + 1):
            for j in range(paper_cumsum[c] + 1):
                T[c, i, j] = 0
                if c > 1:
                    T[c, i, j] = max(T[c, i, j], T[c - 1, i, j])
                if i >= len(components[c][0]) and j >= len(components[c][1]):
                    T[c, i, j] = max(T[c, i, j],
                                     T[c - 1, i - len(components[c][0]), j - len(components[c][1])])
    minimum_max_ratio = num_authors * 2 + num_papers * 2
    best_n0 = 0
    best_m0 = 0
    for i in range(1, num_authors):
        for j in range(1, num_papers):
            if T[n_components - 1, i, j] == 1:
                workload = max((num_papers - j) / i, j / (num_authors - i))
                if workload > max_paper_per_reviewer / min_reviewer_per_paper:
                    continue
                if divide_method == 'workload':
                    this_ratio = workload
                elif divide_method == 'even':
                    this_ratio = max(
                        [i / (num_authors - i), (num_authors - i) / i, j / (num_papers - j), (num_papers - j) / j])
                if this_ratio < minimum_max_ratio:
                    minimum_max_ratio = this_ratio
                    best_n0 = i
                    best_m0 = j
    if minimum_max_ratio > max_paper_per_reviewer / min_reviewer_per_paper:
        return None, None
    # track best option
    solution_best = ([], [])
    author_left = best_n0
    paper_left = best_m0
    for c in range(n_components - 1, 0, -1):
        nt = len(components[c][0])
        mt = len(components[c][1])
        if T[c, author_left, paper_left] == T[c - 1, author_left - nt, paper_left - mt]:
            solution_best[0].extend(components[c][0])
            solution_best[1].extend([-j for j in components[c][1]])
            author_left -= nt
            paper_left -= mt
    if author_left != 0:
        nt = len(components[0][0])
        mt = len(components[0][1])
        assert author_left == nt
        assert paper_left == mt
        solution_best[0].extend(components[0][0])
        solution_best[1].extend([-j for j in components[0][1]])

    solution_another = ([i for i in range(num_authors) if i not in solution_best[0]],
                        [j for j in range(num_papers) if j not in solution_best[1]])
    return solution_best, solution_another


def statistics(components):
    """
    Return the number of connected components and the size of the largest connected component.
    """
    component_sizes = np.asarray([(len(c[0]), len(c[1])) for c in components])
    # order = np.argsort([c[0] + c[1] for c in component_sizes])[::-1]
    order = range(len(components))
    author_sizes = [component_sizes[i][0] for i in order]
    paper_sizes = [component_sizes[i][1] for i in order]
    return len(components), author_sizes, paper_sizes


# BFS for component computation.
def BFS(authors, papers, nodes, tabuset):
    """
    Return a list of connected components.
    @param authors: a list of strings, containing author names. 
    @param papers: is a list of list of strings, where each inner list corresponds to a list of author names. 
    @param nodes: maintains the edge set, where the key is either string (author name) or int (paper id).
    @param: tabuset: Banned reviewers or papers. 
    """
    components = []
    is_visited = set()
    for a in nodes:
        if a in tabuset: continue
        if a in is_visited: continue
        bfs_queue, c = [], [[], []]
        header, tail = 0, 0
        is_visited.add(a)
        bfs_queue.append(a)
        tail += 1
        # Compute for one connected components.
        while tail > header:
            r = bfs_queue[header]
            header += 1
            if r in authors:
                c[0].append(r)
            else:
                c[1].append(r)
            for p in nodes[r]:
                if p in tabuset: continue
                if p in is_visited: continue
                bfs_queue.append(p)
                is_visited.add(p)
                tail += 1
        components.append(c)
    return components
