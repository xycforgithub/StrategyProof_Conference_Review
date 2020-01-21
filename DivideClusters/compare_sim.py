import pickle
import time
from collections import Counter

import numpy as np
from partition import partition
import argparse
from lp import find_match

parser = argparse.ArgumentParser()
parser.add_argument('--compute_random', action='store_true', help='compute random partition.')
args = parser.parse_args()

# parameters
min_reviewer_per_paper = 3
max_paper_per_reviewer = 6
use_first_100 = False  # change to True to test
compute_full = True
num_iters = 1
rand_parti_scores = np.zeros(num_iters)
compute_random = args.compute_random

scores = np.load("../iclr2018_all.npz", allow_pickle=True)
author_idx, paper_idx, smatrix = scores["author_idx"], scores["paper_idx"], scores["similarity_matrix"]
mask_matrix = scores["mask_matrix"]
smatrix *= 1.0 - mask_matrix
data = pickle.load(open('../iclr/2018/papers_info.pkl', 'rb'))

author_idx = author_idx.item()
paper_idx = paper_idx.item()

if use_first_100:
    strip_num = 10  # use first 10(ish) papers
    author_idx = {name: val for name, val in author_idx.items() if val < strip_num}
    paper_idx = {name: val for name, val in paper_idx.items() if val < strip_num}
    smatrix = smatrix[:strip_num, :][:, :strip_num]


def format_name(name):
    return '{}.txt'.format(name)
    # names = name.lower().strip().split(' ')
    # first_name, last_name = names[0], names[-1]


#     print(' '.join((first_name, last_name)))
# return '{}.txt'.format(' '.join((first_name, last_name)))
# filter author list
def format_paper(name):
    return '{}.txt'.format(name)


author_list = []
paper_id_list = []
for slice_data in data.values():
    for pid, l in zip(slice_data[0], slice_data[2]):
        mod_l = [author.strip() for author in l if format_name(author) in author_idx]
        #         if len(mod_l)>0:
        author_list.append(mod_l)
        paper_id_list.append(pid)
    # print(len(slice_data[2]))
author_list = [author_list[paper_idx[format_paper(pid)]] for pid in paper_id_list if format_paper(pid) in paper_idx]
print('num papers:', len(author_list))

# change the smatrix accordingly
c = Counter()
for l in author_list:
    c.update(l)
print('matching authors:', len(c))
# pdb.set_trace()


# do the partition
authors, papers = [], []
degs = {}
num_edges = 0
for ps in author_list:
    papers.append(ps)
    authors.extend(ps)
    for author in ps:
        if author not in degs: degs[author] = 0
        degs[author] += 1
    num_edges += len(ps)
authors = set(authors)

num_authors = len(authors)
num_papers = len(papers)
ars, ds = list(degs.keys()), list(degs.values())
order = np.argsort(ds)[::-1]
# pcounts maintains the number of authors of each paper. 
pcounts = {i: len(papers[i]) for i in range(len(papers))}
pars, pds = list(pcounts.keys()), list(pcounts.values())
porder = np.argsort(pds)[::-1]

print("*" * 50)
print("Number of unique authors", num_authors)
print("Number of papers", num_papers)
print("Number of edges", num_edges)
print("Number of all the nodes in the bipartite graph", num_authors + num_papers)
print("*" * 50)
# Build graph.
# Authors is a list of strings, containing author names. 
# Papers is a list of list of strings, where each inner list corresponds to a list of author names. 
# Nodes maintains the edge set, where the key is either string (author name) or int (paper id).
nodes = {a: [] for a in authors}
for i, p in enumerate(papers):
    for r in p:
        nodes[r].append(i)
    nodes[i] = p

n_author_from_idx = len(author_idx)
ad_mat = np.zeros((n_author_from_idx, num_papers), dtype=int)
for i, a in enumerate(authors):
    target_idx = author_idx[format_name(a)]
    for j in nodes[a]:
        ad_mat[i, j] = 1

for i in range(num_iters):
    if compute_random:
        print('doing random partition')
        par0, par1 = partition(ad_mat, max_paper_per_reviewer, min_reviewer_per_paper, divide_method='random')
    else:
        par0, par1 = partition(ad_mat, max_paper_per_reviewer, min_reviewer_per_paper)

    r0, p0 = par0
    r1, p1 = par1
    # print(r0,p0)
    # print(r1,p1)
    print('lengths:', (len(r0), len(p0)), (len(r1), len(p1)))

    # compute the assignment under unconstrained setting, and then compute average similarity
    if compute_full:
        start_time = time.time()
        original_assignment = find_match(smatrix.T, max_paper_per_reviewer, min_reviewer_per_paper)
        end_time = time.time()
        print(f"Time used to solve the original LP: {end_time - start_time} seconds.")
        original_assignment = original_assignment.T
        sum_sim = np.sum(original_assignment * smatrix)
        print('original total similarity:', sum_sim, 'average:', sum_sim / (n_author_from_idx * max_paper_per_reviewer))

    # compute the assignment under constraint of dividing into two components.
    start_time = time.time()
    par0_sim = smatrix[np.ix_(r0, p0)]
    par0_assign = find_match(par0_sim.T, max_paper_per_reviewer, min_reviewer_per_paper)
    par0_assign = par0_assign.T
    end_time = time.time()
    print(f"Time used to solve the first new LP: {end_time - start_time} seconds.")
    start_time = time.time()
    par1_sim = smatrix[np.ix_(r1, p1)]
    par1_assign = find_match(par1_sim.T, max_paper_per_reviewer, min_reviewer_per_paper)
    par1_assign = par1_assign.T
    end_time = time.time()
    print(f"Time used to solve the second new LP: {end_time - start_time} seconds.")
    sum_sim_par = np.sum(par0_assign * par0_sim) + np.sum(par1_assign * par1_sim)
    mean_score = sum_sim_par / (n_author_from_idx * max_paper_per_reviewer)
    print('divided total similarity:', sum_sim_par, 'average:', mean_score)
    rand_parti_scores[i] = mean_score
print("Finish random partitioning 20 times, save results.")
np.save("random_partition_scores.npy", rand_parti_scores)
print(f"Mean: {np.mean(rand_parti_scores)}, std: {np.std(rand_parti_scores)}")
