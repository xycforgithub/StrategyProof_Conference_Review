import csv
import os

import download_google_scholar_profile as gs

line = 0
with open("authors.csv", "r") as f:
    reader = csv.reader(f, delimiter=",")
    for row in reader:
        author = row[0]
        path = "/tmp/%s/" % author
        link = "https://arxiv.org/search/?query=%s&searchtype=author&abstracts=hide&order=-announced_date_first&size=25" % author
        gs.getArxivReviewer(link, path, [])

        x = 0
        for pdf_file in os.listdir(path):
            pdf_path = path + pdf_file
            print(pdf_path)
            os.system("pdftotext '%s' /tmp/%s.a" % (pdf_path, str(x)))
            x += 1

        print("consolidating files, found in /tmp/authors/%s.txt" % author)
        os.system("cat /tmp/*.a > '/tmp/authors/%s.txt'" % author)
        os.system("rm -r '%s'" % path)
        os.system("rm /tmp/*.a")
