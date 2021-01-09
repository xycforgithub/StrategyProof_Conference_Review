import csv
import os

import download_arxiv as ar

line = 0
with open("authors_rescrape.txt", "r") as f:
    reader = csv.reader(f, delimiter=",")
    for row in reader:
        author = row[0]
        path = "/tmp/%s/" % author
        link = "https://arxiv.org/search/advanced?advanced=&terms-0-operator=AND&terms-0-term=%s&terms-0-field=author&classification-computer_science=y&classification-physics_archives=all&classification-statistics=y&classification-include_cross_list=include&date-filter_by=all_dates&date-year=&date-from_date=&date-to_date=&date-date_type=submitted_date&abstracts=hide&size=50&order=-announced_date_first" % author
        ar.getArxivReviewer(link, path, [])

        os.system("mkdir '/tmp/dump/%s'" % author)

        x = 0
        for pdf_file in os.listdir(path):
            pdf_path = path + pdf_file
            print("PDF: %s" % pdf_path)
            os.system("pdftotext '%s' '/tmp/dump/%s/%s.a'" % (pdf_path, author, str(x)))
            x += 1

        print("consolidating files to /tmp/authors/%s.txt" % author)
        for i in range(x):
            os.system("cat '/tmp/dump/%s/%s.a' >> '/tmp/authors/%s.txt'" % (author, i, author))
        os.system("rm -r '%s'" % path)
        # os.system("rm /tmp/dump/*.a")    save the text of pdfs
