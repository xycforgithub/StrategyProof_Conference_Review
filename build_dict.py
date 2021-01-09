#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Author: hanzhao
# Email: han.zhao@cs.cmu.edu
# Date: 2019-04-30
"""
Build the inverse document frequency dictionary for all the terms.
"""
import csv
import glob
import math
import os
import time
from collections import Counter
from collections import defaultdict

import numpy as np
import pandas as pd
from nltk.stem import PorterStemmer

from tpms.pdf2bow import tokenize, isUIWord


def paper2bow(text):
    """
    Tokenize and filter.
    :param text: string. Collection of texts from each paper.
    :return: map: string->int.
    """
    words = [w.lower() for w in tokenize(text)]
    # Filter out uninformative words.
    words = filter(lambda w: not isUIWord(w), words)
    # Use PortStemmer.
    ps = PorterStemmer()
    words = [ps.stem(w) for w in words]
    return Counter(words)


def is_written_by(author_first_name, author_last_name, paper):
    """
    Judge whether the scraped paper belongs to the given author or not. 
    :param author_first_name:     string. First name of the author.
    :param author_last_name:    string. Last name of the author.
    :param paper:   string. arXiv papers scraped online.
    """
    if (paper.find(author_first_name) >= 0 and paper.find(author_last_name) >= 0) and len(paper) > 0:
        return True
    else:
        return False


def build_mask(author_idx, paper_idx, paper_info):
    """
    Build a binary matrix of author-paper, where 1 indicates a conflict between the corresponding author and paper.
    :param author_idx:   dict[author_name -> index]
    :param paper_idx:    dict[paper_name -> index]
    :paper_info:    dict[paper_idx -> list of authors]
    :return: Binary mask matrix corresponding to the conflict graph.
    """
    num_author, num_paper = len(author_idx), len(paper_idx)
    mask_matrix = np.zeros((num_author, num_paper), dtype=np.int8)
    filtered_authors = set()
    for (p, j) in paper_idx.items():
        pid = p.split(".")[0]
        authors = paper_info[pid]
        for author in authors:
            aid = author + ".txt"
            if aid not in author_idx:
                filtered_authors.add(author)
            else:
                i = author_idx[aid]
                mask_matrix[i, j] = 1
    print("Number of filtered reviewers: {}".format(len(filtered_authors)))
    print("Number of effective links: {}".format(np.sum(mask_matrix[:])))
    return mask_matrix


def parse_papers(author_folder, paper_folder):
    """
    Convert each text file into a counter.
    :param author_folder:   Path of the folder that contains all the texts of authors.
    :param paper_folder:    Path of the folder that contains all the texts of papers.
    :return: list[map: string->int]
    """
    current_folder = os.getcwd()
    all_words = set()
    authors, papers = {}, {}
    # Parse all the authors.
    os.chdir(author_folder)
    cnt = 0
    print("Processing all the authors...")
    start_time = time.time()
    for textfile in glob.glob("*.txt"):
        author_name = textfile.split(".")[0].lower().split(" ")
        first_name, last_name = author_name[0], author_name[-1]
        cnt += 1
        if cnt % 100 == 0:
            print("Processed {} authors.".format(cnt))
        with open(textfile, "r", encoding="utf-8") as fin:
            text = fin.read().lower()
            if is_written_by(first_name, last_name, text):
                counter = paper2bow(text)
                authors[textfile] = counter
    end_time = time.time()
    print("Total number of arXiv authors without filtering: {}.".format(cnt))
    print("Total number of arXiv authors after removing the invalid: {}".format(len(authors)))
    print("Total time used for processing authors: {} seconds.".format(end_time - start_time))
    print("Processing all the papers...")
    start_time = time.time()
    os.chdir(current_folder)
    # Parse all the arxiv papers. 
    os.chdir(paper_folder)
    cnt = 0
    for textfile in glob.glob("*.txt"):
        cnt += 1
        if cnt % 100 == 0:
            print("Processed {} papers.".format(cnt))
        with open(textfile, "r", encoding="utf-8") as fin:
            text = fin.read().lower()
            counter = paper2bow(text)
            papers[textfile] = counter
    end_time = time.time()
    print("Total number of submitted papers: {}.".format(len(papers)))
    print("Total time used for processing papers: {} seconds.".format(end_time - start_time))
    # Combine all the unique words from both papers and authors.
    for author in authors:
        all_words |= set(authors[author].keys())
    for paper in papers:
        all_words |= set(papers[paper].keys())
    print("Number of unique words in the dictionary: {}.".format(len(all_words)))
    # Computing the idf of each unique word.
    N = len(authors) + len(papers)
    print("Total number of documents = {}".format(N))
    idf = defaultdict(lambda: 0.0)
    for author in authors:
        for word in authors[author]:
            idf[word] += 1.0
    for paper in papers:
        for word in papers[paper]:
            idf[word] += 1.0
    for word in idf:
        idf[word] = math.log(N / idf[word])
    assert len(all_words) == len(idf)
    # Use the order in idf.keys() as the default mapping from word to index. 
    print("Start building similarity matrix...")
    start_time = time.time()
    os.chdir(current_folder)
    num_authors = len(authors)
    num_papers = len(papers)
    author_idx = dict(zip(authors.keys(), list(range(num_authors))))
    paper_idx = dict(zip(papers.keys(), list(range(num_papers))))
    similarity_matrix = -np.ones((num_authors, num_papers))
    # mask_matrix = np.zeros((num_authors, num_papers))
    for author in authors:
        for paper in papers:
            aid, pid = author_idx[author], paper_idx[paper]
            avec, pvec = authors[author], papers[paper]
            if len(avec) == 0 or len(pvec) == 0:
                continue
            a_tot, p_tot = max(avec.values()), max(pvec.values())
            sim = 0.0
            # Compute the L2 norm of both avec and pvec.
            avec_norm, pvec_norm = 0.0, 0.0
            for word in avec:
                a_tf = 0.5 + 0.5 * avec[word] / a_tot
                w_idf = idf[word]
                avec_norm += (a_tf * w_idf) ** 2
                if word in pvec:
                    # Augmented term frequency to prevent a bias towards longer document.
                    p_tf = 0.5 + 0.5 * pvec[word] / p_tot
                    sim += a_tf * p_tf * (w_idf ** 2)
            for word in pvec:
                p_tf = 0.5 + 0.5 * pvec[word] / p_tot
                w_idf = idf[word]
                pvec_norm += (p_tf * w_idf) ** 2
            # Compute the cosine angle as the similarity score.
            avec_norm, pvec_norm = math.sqrt(avec_norm), math.sqrt(pvec_norm)
            similarity_matrix[aid, pid] = sim / avec_norm / pvec_norm
    end_time = time.time()
    print("Time used to build similarity matrix: {} seconds.".format(end_time - start_time))
    return author_idx, paper_idx, similarity_matrix


if __name__ == "__main__":
    # author_idx, paper_idx, similarity_matrix = parse_papers("./authors-rescrape", "./iclr/2018/papers")
    # np.savez("iclr2018.npz", author_idx=author_idx, paper_idx=paper_idx, similarity_matrix=similarity_matrix)
    # print("*" * 50)

    iclr2018 = np.load("iclr2018.npz")
    author_idx, paper_idx, similarity_matrix = iclr2018["author_idx"], iclr2018["paper_idx"], iclr2018[
        "similarity_matrix"]
    author_idx, paper_idx = author_idx.item(), paper_idx.item()
    # Load the meta-information of all the papers from ICLR 2018.
    paper_info = {}
    with open("iclr/2018/papers_info.csv", "r") as csvfile:
        csv_reader = csv.reader(csvfile)
        for p in csv_reader:
            paper_info[p[0]] = p[3:]
            assert len(p[3:]) > 0
    print("Number of authors: {}".format(len(author_idx)))
    print("Number of papers: {}".format(len(paper_idx)))
    print("Maximum similarity value: {}".format(np.max(similarity_matrix)))
    print("Minimum similarity value: {}".format(np.min(similarity_matrix[similarity_matrix > 0.0])))
    print("Author index: {}".format(author_idx))
    print("Paper index: {}".format(paper_idx))
    print("Paper meta-info: {}".format(paper_info))
    scores = pd.DataFrame(similarity_matrix)
    #     anames, pnames = list(range(len(author_idx))), list(range(len(paper_idx)))
    #     for a in author_idx:
    #         anames[author_idx[a]] = a
    #     for p in paper_idx:
    #         pnames[paper_idx[p]] = p
    #     scores.describe()
    #     # scores.to_csv("./iclr2018_scores.csv")
    mask_matrix = build_mask(author_idx, paper_idx, paper_info)
    print("Binary mask matrix: {}".format(np.sum(mask_matrix, axis=0)))
    assert mask_matrix.shape == similarity_matrix.shape
    np.savez("iclr2018_all.npz", author_idx=author_idx, paper_idx=paper_idx, similarity_matrix=similarity_matrix,
             mask_matrix=mask_matrix)
    scores.to_csv("./iclr2018_scores.csv")
