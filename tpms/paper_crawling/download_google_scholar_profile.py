# This Python file uses the following encoding: utf-8

import datetime
import os
import re
import time
import unicodedata

from bs4 import BeautifulSoup
from numpy import random


# suggested by http://stackoverflow.com/questions/1342000/how-to-replace-non-ascii-characters-in-string
def removeNonAscii(s): return "".join(i for i in s if ord(i) < 128)


def sanitize(w, inputIsUTF8=False, expungeNonAscii=False):
    map = {'æ': 'ae',
           'ø': 'o',
           '¨': 'o',
           'ß': 'ss',
           'Ø': 'o',
           '\xef\xac\x80': 'ff',
           '\xef\xac\x81': 'fi',
           '\xef\xac\x82': 'fl'}

    # This replaces funny chars in map
    for char, replace_char in list(map.items()):
        w = re.sub(char, replace_char, w)

    # w = unicode(w, encoding='latin-1')
    if inputIsUTF8:
        w = str(w, encoding='utf-8', errors='replace')

    # This gets rid of accents
    w = ''.join((c for c in unicodedata.normalize('NFD', w) if unicodedata.category(c) != 'Mn'))

    if expungeNonAscii:
        w = removeNonAscii(w)

    return w


def fileHash(filename_loc):
    f = open(filename_loc, 'r')
    import hashlib
    h = hashlib.md5()
    h.update(f.read())
    f.close()

    return h.hexdigest()


def alreadyInReviewerProfile(filename_loc, reviewerFiles):
    return False
    # if fileHash(filename_loc) in reviewerFiles:
    #    return True
    # else:
    #    return False


def getPage(url, outFileName, link_name=None):
    print(("Call to getPage"))
    if re.search('arxiv\.org', url):
        arxiv_timeout = 3
        print(('\tRetrieving from arxiv.org, waiting %d seconds' % arxiv_timeout))
        time.sleep(arxiv_timeout)
        time.sleep(random.random())
        # return False

    if not os.path.exists(outFileName):
        useragent = '"Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.8) Gecko/20100225 Iceweasel/3.5.8 (like Firefox/3.5.8)"'
        print(('\tRetrieving:', url))
        # print """wget --quiet --no-use-server-timestamps -U %s --timeout=10 -t 1 -O %s '%s'""" % (useragent, outFileName, url)
        os.system("""wget --quiet --no-use-server-timestamps -U %s --timeout=10 -t 1 -O %s '%s'""" % (
            useragent, outFileName, url))
        if not os.path.exists(outFileName):
            print('could not retrieve file')
            return False
        elif os.path.getsize(outFileName) == 0:
            print('retrieved file has zero length')
            return False
    else:
        print(('\t', outFileName, 'already exists'))

    if link_name is not None:
        if os.path.exists(link_name):
            if os.path.islink(link_name):
                os.remove(link_name)
                print(('removing link', link_name))
            else:  # this is to deal with previously retrieved files before we used the symbolic link
                stat = os.stat(link_name)
                t = re.sub('\.html$', '', link_name) + '_' + datetime.datetime.fromtimestamp(stat.st_atime).strftime(
                    '%Y-%m-%d-%H%M%S') + '.html'
                print(('renaming link', link_name, 'to', t))
                os.rename(link_name, t)
        print(('creating link', link_name, 'to', os.path.basename(outFileName)))
        os.symlink(os.path.basename(outFileName), link_name)

    return True


def createDir(dirloc):
    if not os.path.isdir(dirloc):
        try:
            os.mkdir(dirloc)
        except OSError:
            print(('failed to directory', dirloc))
            return


def getReviewer(gScholarURL, reviewerEmail, reviewerDir, reviewerFiles, reviewerTmpDir='/tmp/gscholar_dl/',
                numPapersToRetrieve=1000):
    """ Downloads a reviewer's paper given his Google Scholar profile URL
     In:
     gscholarURL: URL of google scholar profile, if empty string then will use the latest downloaded profile
     reviewerEmail: email address of reviewer
     reviewerDir: directory in which to store the papers
    """

    # reviewerTmpDir=tmpDir+reviewerEmail+'/'

    createDir(reviewerDir)
    createDir(reviewerTmpDir)

    if len(gScholarURL) > 0:
        # Save info to a reviewer file 
        st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H%M%S')
        f = open('%sgscholar_url_%s.csv' % (reviewerTmpDir, st), 'w')
        f.write('%s,%s\n' % (reviewerEmail, gScholarURL))
        f.close()

        reviewerFileLocLink = reviewerTmpDir + reviewerEmail + '.html'
        reviewerFileLoc = reviewerTmpDir + reviewerEmail + '_' + st + '.html'
        if not getPage(gScholarURL, reviewerFileLoc, link_name=reviewerFileLocLink):
            print('problem retrieving link')
            return
    else:
        print("Got empty reviewer scholar URL, using most recent one")
        reviewerFileLoc = os.path.realpath(reviewerTmpDir + reviewerEmail + '.html')
        if not os.path.exists(reviewerFileLoc):
            print(("Could not find reviewers' profile", reviewerFileLoc))

        # get most recent profile file
        # try:
        #    reviewerFileLoc = max(glob.glob('%sgscholar_url*.csv' % reviewerTmpDir))
        # except ValueError:
        #    print "Could not find reviewers' profile", reviewerTmpDir
        #    return  
        print(reviewerFileLoc)

    f = open(reviewerFileLoc, 'r')
    bs = BeautifulSoup(''.join(f.read()), features="html.parser")
    f.close()

    # papers = bs.find_all(attrs={"class": "cit-table item"})
    papers = bs.find_all(attrs={"class": "gsc_a_tr"})
    print(('found', len(papers), 'papers from', reviewerEmail))
    if numPapersToRetrieve < len(papers):
        papers = papers[:numPapersToRetrieve]
        print(('\tLimiting retrieval to %d papers' % len(papers)))
    for j, paper in enumerate(papers):
        print(('PAPER:', j))
        for i, td in enumerate(paper.find_all('td')):
            if i == 0:  # paper title, link, author names.
                print("LOOKING FOR PAPER TO DOWNLOAD")
                paper_page_url = 'http://scholar.google.com' + td.a.get('data-href')
                paper_title = td.a.string
                print(('\tlink', paper_page_url))
                print(('\tauthors', papers[0].td.span.string))
                print(('\ttitle:', paper_title))

                filename_title = sanitize(re.sub('[\W]', '_', paper_title), expungeNonAscii=True,
                                          inputIsUTF8=False) + '.pdf'
                if len(filename_title + '.html') > 255:  # ext4 limits the length of filenames
                    filename_title = filename_title[:240] + '%06d' % random.randint(100000) + '.pdf'
                paper_loc = reviewerTmpDir + filename_title + '.html'
                print("1: CALLING GETPAGE")
                print(paper_page_url)

                sleep(randint(3, 5))
                getPage(paper_page_url, paper_loc)
                f = open(paper_loc, 'r')
                doc = f.read()
                f.close()
                bs_paper = BeautifulSoup(''.join(doc), features="html.parser")
                if bs_paper.find_all(text="[PDF]"):
                    print("1.5: find_all")
                    paper_pdf_url = bs_paper.find_all(text="[PDF]")[0].findPrevious('a')['href']
                    filename_tmp_loc = reviewerTmpDir + filename_title
                    filename_loc = reviewerDir + filename_title
                    if not os.path.exists(filename_loc) or os.path.getsize(filename_loc) == 0:
                        print("2: CALLING GETPAGE")
                        if getPage(paper_pdf_url, filename_tmp_loc):
                            if not alreadyInReviewerProfile(filename_tmp_loc, reviewerFiles):
                                print('\tAdding file to reviewer profile')
                                print("filename_loc")
                                os.rename(filename_tmp_loc, filename_loc)
                            else:
                                print('\tfile with identical hash already exists')
                        else:
                            print('\tunable to download paper')
                    else:
                        print('\tpaper previously downloaded')
                else:
                    print('\tno PDF link')
            elif i == 1:  # citations
                if td.a is not None:
                    num_citations = td.a.string
                else:
                    num_citations = 0
                print(('\tnum. citations', num_citations))
            elif i == 2:  # empty
                pass
            elif i == 3:  # year
                if td.string is not None:
                    year = td.string
                else:
                    year = 'na'
                print(('\tyear', year))


def getArxivReviewer(arxivURL, reviewerDir, reviewerFiles, reviewerTmpDir='/tmp/arxiv_dl/',
                     numPapersToRetrieve=10):
    """ Downloads a reviewer's paper given his Google Scholar profile URL
     In:
     gscholarURL: URL of google scholar profile, if empty string then will use the latest downloaded profile
     reviewerEmail: email address of reviewer
     reviewerDir: directory in which to store the papers
    """

    # reviewerTmpDir=tmpDir+reviewerEmail+'/'

    createDir(reviewerDir)
    createDir(reviewerTmpDir)

    if len(arxivURL) > 0:
        # Save info to a reviewer file 
        st = datetime.datetime.fromtimestamp(time.time()).strftime('%Y-%m-%d-%H%M%S')
        f = open('%sarxiv_url_%s.csv' % (reviewerTmpDir, st), 'w')
        f.write('%s\n' % (arxivURL))
        f.close()

        reviewerFileLocLink = reviewerTmpDir + '.html'
        reviewerFileLoc = reviewerTmpDir + '_' + st + '.html'
        if not getPage(arxivURL, reviewerFileLoc, link_name=reviewerFileLocLink):
            print('problem retrieving link')
            return
    else:
        print("Got empty arxiv URL, using most recent one")
        reviewerFileLoc = os.path.realpath(reviewerTmpDir + '.html')
        if not os.path.exists(reviewerFileLoc):
            print(("Could not find reviewers' profile", reviewerFileLoc))

        # get most recent profile file
        # try:
        #    reviewerFileLoc = max(glob.glob('%sgscholar_url*.csv' % reviewerTmpDir))
        # except ValueError:
        #    print "Could not find reviewers' profile", reviewerTmpDir
        #    return  

    print(reviewerFileLoc)
    f = open(reviewerFileLoc, 'r')
    bs = BeautifulSoup(''.join(f.read()), features="html.parser")
    f.close()

    # papers = bs.find_all(attrs={"class": "cit-table item"})
    papers = bs.find_all(attrs={"class": "arxiv-result"})
    print(('found', len(papers), 'papers from', arxivURL))
    if numPapersToRetrieve < len(papers):
        papers = papers[:numPapersToRetrieve]
        print(('\tLimiting retrieval to %d papers' % len(papers)))
    for j, paper in enumerate(papers):
        print(('PAPER:', j))

        if paper.div.p.span.find_all(text="pdf"):
            print("1: LOOKING FOR PDF LOCATION")
            paper_pdf_url = paper.div.span.find_all(text="pdf")[0].findPrevious('a')['href']
            print(paper_pdf_url)

            for i, p in enumerate(paper.find_all('p')):
                if i == 1:  # paper title
                    print("2: LOOKING FOR PAPER TITLE")
                    print(p.string)
                    paper_title = p.string.strip()

                    filename_title = sanitize(re.sub('[\W]', '_', paper_title), expungeNonAscii=True,
                                              inputIsUTF8=False) + '.pdf'
                    if len(filename_title + '.html') > 255:  # ext4 limits the length of filenames
                        filename_title = filename_title[:240] + '%06d' % random.randint(100000) + '.pdf'
                    paper_loc = reviewerTmpDir + filename_title + '.html'
                    filename_tmp_loc = reviewerTmpDir + filename_title
                    filename_loc = reviewerDir + filename_title
                    if not os.path.exists(filename_loc) or os.path.getsize(filename_loc) == 0:
                        print("3: DOWNLOADING PDF")
                        if getPage(paper_pdf_url, filename_tmp_loc):
                            if not alreadyInReviewerProfile(filename_tmp_loc, reviewerFiles):
                                print('\tAdding file to reviewer profile')
                                print("filename_loc")
                                os.rename(filename_tmp_loc, filename_loc)
                            else:
                                print('\tfile with identical hash already exists')
                        else:
                            print('\tunable to download paper')
                    else:
                        print('\tpaper previously downloaded')
        else:
            print("NO PDF")
