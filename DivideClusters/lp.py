import time
import numpy as np
from scipy.sparse import csr_matrix
from cvxopt import matrix, spmatrix, solvers


def find_match(S, max_paper_per_reviewer=6, min_reviewer_per_paper=3):
    """
    Solve the corresponding linear program to compute the paper-reviewer assignments.
    :param S:   np.array, 2d matrix of shape n_papers x n_reviewers, the similarity matrix.
    :param max_paper_per_reviewer:  # papers that each reviewer can review.
    :param min_reviewer_per_paper:  # reviewers that each paper should be reviewed.
    :return:    Matching. Solve the standard minimization problem using LP formulation.
    """
    (num_papers, num_reviewers) = S.shape
    print(f"# papers = {num_papers}, # reviewers = {num_reviewers}")
    mu = max_paper_per_reviewer
    lambd = min_reviewer_per_paper

    c = np.zeros(num_papers * num_reviewers, dtype=np.double)
    for i in range(num_papers):
        for j in range(num_reviewers):
            c[i * num_reviewers + j] = -S[i][j]
    print("Constructing the sparse constraint matrix:")
    num_cons = num_papers + num_reviewers + 2 * num_papers * num_reviewers
    num_vars = num_papers * num_reviewers
    print(f"# Optimization variables: {num_vars}, # Optimization constraints: {num_cons}")
    # Number of non-zero values in the matrix: n * m + n * m + 2 * n * m = 4 * n * m.
    i_idx = np.arange(4 * num_papers * num_reviewers, dtype=np.int64)
    j_idx = np.zeros(4 * num_papers * num_reviewers, dtype=np.int64)
    dvals = np.zeros(4 * num_papers * num_reviewers, dtype=np.int8)
    bvals = np.zeros(num_cons, dtype=np.double)
    for k in range(4 * num_papers * num_reviewers):
        if k < num_papers * num_reviewers:
            # Constraints to ensure that num_reviewers per paper at least lambd.
            i = k // num_reviewers
            j = k % num_reviewers
            i_idx[k], j_idx[k] = i, i * num_reviewers + j
            dvals[k] = -1
            bvals[i_idx[k]] = -lambd
        elif k < 2 * num_papers * num_reviewers:
            # Constraints to ensure that num_papers per reviewer at most mu.
            kprime = k - num_papers * num_reviewers
            i = kprime // num_papers
            j = kprime % num_papers
            i_idx[k], j_idx[k] = num_papers + i, j * num_reviewers + i
            dvals[k] = 1
            bvals[i_idx[k]] = mu
        elif k < 3 * num_papers * num_reviewers:
            # Constraints to ensure that >= 0.
            kprime = k - 2 * num_papers * num_reviewers
            i_idx[k], j_idx[k] = num_papers + num_reviewers + kprime, kprime
            dvals[k] = -1
            bvals[i_idx[k]] = 0
        else:
            # Constraints to ensure that <= 1.
            kprime = k - 3 * num_papers * num_reviewers
            base = num_papers + num_reviewers + num_papers * num_reviewers
            i_idx[k], j_idx[k] = kprime + base, kprime
            dvals[k] = 1
            bvals[i_idx[k]] = 1
    A = csr_matrix((dvals, (i_idx, j_idx)), shape=(num_cons, num_vars)).tocoo()
    G = spmatrix(A.data.tolist(), A.row.tolist(), A.col.tolist(), size=A.shape)
    obj = matrix(c.reshape(-1, 1))
    b = matrix(bvals.reshape(-1, 1))
    print(f"Shape of the constraint matrix: {A.shape}")
    print("Start solving the LP:")
    start_time = time.time()
    # sol = solvers.lp(obj, G, b, solver="glpk")
    sol = solvers.lp(obj, G, b, solver="mosek")
    end_time = time.time()
    print(f"Time used to solve the LP: {end_time - start_time} seconds.")
    opt_x = np.array(sol["x"]).reshape(num_papers, num_reviewers)
    return opt_x


if __name__ == '__main__':
    S = np.array([[3, 2, 5], [0, 4, 1], [2, 4, 0], [2, 2, 1]])
    print(find_match(S, max_paper_per_reviewer=2, min_reviewer_per_paper=1))
