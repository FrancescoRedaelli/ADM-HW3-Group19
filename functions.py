### Libraries & Setup

import requests   # HTTP requests
from bs4 import BeautifulSoup   # HTML documents parsing

import pandas as pd
import numpy as np   # Scientific Computing
from datetime import datetime   # Date and Time manipulation
from collections import defaultdict   # Dictionary with default value
import csv   # CSV and TSV handling
import re   # Regular Expressionsx

import matplotlib.pyplot as plt   # Visualization
import os   # Operating System interaction

import warnings
warnings.filterwarnings('ignore')

###[1.1]

def collect_urls(filename):

    '''
    Retrieve all URLs of the "Most popular places" places listed in the first $400$ pages and store them in the filename.txt file
    '''

    with open(filename, 'w') as f:
        for i in range(400):
            # Build URL for page i+1
            url = "https://www.atlasobscura.com/places?page={}&sort=likes_count".format(i+1)
            # GET request
            list_page = requests.get(url)
            # Retrieve HTML text
            list_soup = BeautifulSoup(list_page.text, features="lxml")
            # Collect URLs of places listed
            list_places = ["https://www.atlasobscura.com" + x.get("href") for x in list_soup.find_all("a", {"class": "content-card-place"})]

            # Write URLs to .txt file
            for line in list_places:
                f.write(f"{line}\n")

###[1.2]

def collect_html_pages(url_pair):

    '''
    Retrieve HTML content from the input URL and store it into a .html file, saved in the proper folder
    (according to the page in which the URL was listed)
    INPUT: (URL, URL index)
    '''

    # Importing necessary libraries (needed for multiprocessing)
    import requests
    from bs4 import BeautifulSoup
    import os

    # Unpacking input values
    url, index = url_pair

    # GET request
    result = requests.get(url)
    # Retrieve HTML text
    list_soup = BeautifulSoup(result.text, features="lxml")

    # Compute document and page index
    doc_id = index + 1
    page_id = index//18 + 1

    # Build directory name
    dirName = "HTML_Pages\Page{}".format(page_id)

    # Create directory (if non-existent)
    if not os.path.exists(dirName): os.makedirs(dirName)

    # Create HTML file
    with open(dirName+"\Doc{}.html".format(doc_id), 'w', encoding='utf-8') as f:
        f.write(str(list_soup))

###[1.3]

def parse_page(index, urls_list):

    '''
    Extract desired information from the target HTML page and store them into a .tsv file
    '''

    # Open HTML file
    with open("HTML_Pages\Page{}\Doc{}.html".format(index//18 + 1, index + 1), "r", encoding='utf-8') as f:

        # Read file content
        text = f.read()

        # BeautifulSoup object
        soup = BeautifulSoup(text, features="lxml")

        # Extract information
        placeName = soup.find_all("h1", {"class": "DDPage__header-title"})[0].contents[0].strip()

        placeTags = [x.contents[0].strip() for x in soup.find_all("a", {"class": "js-item-tags-link"})]

        numPeopleVisited = soup.find_all("div", {"class": "item-action-count"})[0].contents[0]

        numPeopleWant = soup.find_all("div", {"class": "item-action-count"})[1].contents[0]

        placeDesc = [" ".join(x.text.strip().replace("\xa0","").split()) for x in soup.find_all("div", {"id": "place-body"})].pop()

        placeShortDesc = " ".join(soup.find_all("h3", {"class": "DDPage__header-dek"})[0].contents[0].strip().replace("\xa0","").split())

        placeNearby = list(set([x.contents[0].strip() for x in soup.find_all("div", {"class": "DDPageSiderailRecirc__item-title"})]))

        placeAddress = " ".join(str(soup.find_all("address", {"class": "DDPageSiderail__address"})[0]).split("<div>")[1].strip().replace("<br/>"," - ").split())

        placeAlt = float(soup.find("div", {"class": "DDPageSiderail__coordinates"})["data-coordinates"].split(",")[0].strip())

        placeLong = float(soup.find("div", {"class": "DDPageSiderail__coordinates"})["data-coordinates"].split(",")[1].strip())

        try:
            placeEditors = list(set([soup.find("a", {"class": "DDPContributorsList__contributor"}).contents[0].strip()] + [x.contents[0].strip() for x in [x.find("span") for x in soup.find_all("a", {"class": "DDPContributorsList__contributor"}) if x.find("span") is not None]]))
        except:
            placeEditors = []

        try:
            placePubDate = datetime.strptime(str(soup.find_all("div", {"class": "DDPContributor__name"})[0].contents[0]), "%B %d, %Y")
        except:
            placePubDate = []

        try:
            placeRelatedLists = [x.contents[0].strip() for x in [x.find("span") for x in soup.find_all("a", {"class": "Card --content-card-v2 --content-card-item Card--list"}) if x.find("span") is not None]]
        except:
            placeRelatedLists = []

        try:
            placeRelatedPlaces = [x.contents[0].strip() for x in (x.find_all("span") for x in soup.find_all("div", {"class": "full-width-container CardRecircSection"}) if str(x.find("div", {"class": "CardRecircSection__title"}).contents[0])=="Related Places").__next__()]
        except:
            placeRelatedPlaces = []

        placeURL = urls_list[index]

        # Build TSV line
        data = [placeName, placeTags, numPeopleVisited, numPeopleWant, placeDesc, placeShortDesc, placeNearby, placeAddress, placeAlt, placeLong, placeEditors, placePubDate, placeRelatedLists, placeRelatedPlaces, placeURL]

        # Convert empty lists to empty strings (for easier TSV decoding)
        for i in range(len(data)):
            if isinstance(data[i], list) and len(data[i])==0: data[i]=""

        # Create TSV file
        with open("TSV_Files\place_{}.tsv".format(index+1), 'w', encoding='utf-8') as f:
            tsv_writer = csv.writer(f, delimiter="\t", quotechar=None)
            tsv_writer.writerow(data)

###[2]

def check_empty(a):
    if len(a) == 0:
        return False
    else:
        return True

def pre_process(path, stemmer):

    '''
    Document "placeDesc" field preprocessing
    '''

    Description = defaultdict(str)
    curr_path = os.getcwd()
    os.chdir(path)
    files = os.listdir()
    for file_name in files:
        f = open(file_name, 'r', encoding='utf-8')
        a = f.read()
        a = re.split(r'\t+', a)
        a_sub = a[4]
        a_sub = re.split('\?|\.|; |, |\*|\n|! |\t| |\(|\)|- ', a_sub)
        a_sub = list(filter(check_empty, a_sub))
        for i in range(len(a_sub)):
            a_sub[i] = stemmer.stem(a_sub[i]).lower()
        Description[file_name] = ' '.join(a_sub)
        f.close()

    os.chdir(curr_path)
    return Description

###[2.1.1]

def build_inv_idx(collection, vocabulary):

    '''
    Build inverted index
    '''

    inv_idx = defaultdict(set)

    for i in collection:
        descr_list = set(collection[i].split())
        for word in descr_list:
            term_i = vocabulary[word]
            inv_idx[term_i].add(i)

    return inv_idx

###[2.1.2]

def searchText(path, query, inverted_index, vocabulary):

    '''
    Execute input query and output result
    '''

    curr_path = os.getcwd()
    os.chdir(path)
    docs = inverted_index[vocabulary[query[0]]]
    for word in query:
        docs = docs.intersection(inverted_index[vocabulary[word]])
    result = pd.DataFrame(columns = ['Title', 'Description', 'URL'])
    for i in docs:
        f = open(i , "r", encoding="utf8")
        a = f.read()
        a = re.split(r'\t', a)
        result = result.append({'Title': a[0].strip(),'Description': a[4].strip(), 'URL': a[14].strip() }, ignore_index=True)
        f.close()
    os.chdir(curr_path)
    return result, docs

def build_inv_idx2(important_words, vocabulary, inverted_index, files, result, names):

    '''
    Build inverted index with tfidf
    '''

    inverted_index2 = defaultdict(set)
    for i in important_words:
        term_id = vocabulary[i]
        score_list = [x[0] for x in np.array(result[:, names.index(i)])]
        for doc in inverted_index[term_id]:
            index = files.index(doc)
            score = score_list[index]
            inverted_index2[term_id].add((doc, score))

###[7]

def read_input():

    '''
    Read 'ApplicantsInfo.txt' input file
    '''

    f = open("ApplicantsInfo.txt", "r")
    n,m = map(int, f.readline().split())
    applicants_info = defaultdict(list)
    for i in range(n):
        x = f.readline()
        a = np.array(x.split())
        score = sum(map(int,a[2:]))/m
        applicants_info[score].append(' '.join(a[:2]))
    f.close()
    return applicants_info

def write_output(data):

    '''
    Write 'RankingList.txt' output file
    '''

    f = open('RankingList.txt', 'w')
    for i in range(len(data)):
        if len(data[i][1]) == 1:
            f.write(str(*data[i][1]))
            f.write(' ')
            f.write(str(data[i][0]))
            f.write('\n')
        else:
            for j in data[i][1]:
                f.write(str(j))
                f.write(' ')
                f.write(str(data[i][0]))
                f.write('\n')
    f.close()
    return

def plot_time(times, alph=False, mp=False):

    '''
    Plot execution time of sorting algorithms
    '''

    # Plot
    f = plt.figure()
    plt.ylabel("Time (s)", fontsize=14, labelpad=20)
    plt.xlabel("Algorithm", fontsize=14, labelpad=20)
    if alph: plt.title("Execution time to sort data by score and name", fontsize=18, pad=15)
    else: plt.title("Execution time to sort data by score", fontsize=18, pad=15)
    if mp: plt.bar(["BubbleSort", "SelectionSort", "QuickSort", "MapReduce"], times, width=0.8,
                   color=['#00ccff', '#00ccff', '#00ccff','#ff6600'], ec="k")
    else: plt.bar(["BubbleSort", "SelectionSort", "QuickSort"], times, width=0.8, color='#00ccff', ec="k")
    f.set_figwidth(14)
    f.set_figheight(8)

    return