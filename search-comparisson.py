import time
import sys
import string
import re
from textblob import TextBlob
from polyglot.text import Text
import pymongo
from pymongo import MongoClient
from suffix_trees import STree

import file_scanner
import file_to_db
import file_reader


""" Boyer Moore string search algorithm """
class last_occurrence(object):
    """Last occurrence functor."""

    def __init__(self, pattern, alphabet):
        """Generate a dictionary with the last occurrence of each alphabet
        letter inside the pattern.
        
        Note: This function uses str.rfind, which already is a pattern
        matching algorithm. There are more 'basic' ways to generate this
        dictionary."""
        self.occurrences = dict()
        for letter in alphabet:
            self.occurrences[letter] = pattern.rfind(letter)

    def __call__(self, letter):
        """Return last position of the specified letter inside the pattern.
        Return -1 if letter not found in pattern."""
        return self.occurrences[letter]

def boyer_moore_match(text, pattern):
    """Find occurrence of pattern in text."""
    alphabet = set(text)
    last = last_occurrence(pattern, alphabet)
    m = len(pattern)
    n = len(text)
    i = m - 1  # text index
    j = m - 1  # pattern index
    while i < n:
        if text[i] == pattern[j]:
            if j == 0:
                return text[i]
            else:
                i -= 1
                j -= 1
        else:
            l = last(text[i])
            i = i + m - min(j, 1+l)
            j = m - 1 
    return -1


""" Horspool string search algorithm """
# preprocess - initialize occ
def preprocess(pattern):
    occ = dict.fromkeys(string.ascii_lowercase, -1)
    for i in range(0,len(pattern)-1):
        occ[pattern[i]] = i
    return occ

# seach - find string with horspool
def horspool_search(text,pattern,occ):
    found = 0
    i = 0
    m = len(pattern)
    n = len(text)

    while i <= n-m:
        j = m-1
        while j >= 0 and pattern[j] == text[i+j]:
            j = j-1
        if j < 0:
            found = found+1
            print("found!")
        i = i + m-1
        i = i - occ[text[i]]
    return found

""" Knutt-Morris-Pratt """
def kmp_search(text, pattern):
    d = {0:0}
    template = pattern + '#' + text
    for i in range(1,len(template)):
        j = d[i-1]
        while j > 0 and template[j] != template[i]:
            j = d[j-1]
        if template[j] == template[i]:
            j += 1
        d[i] = j
        if j == len(pattern):
            return i
    return None 

"""def string_search(text, pattern):
    i=j=0
    lengthS = len(text)
    lengthX = len(pattern)
    while i<=lengthS - lengthX and j>lengthX:
        if li[i+j]==x[j]:
            j+=1
        
        else:
            i+=1
            j=0
    
    return i if j==lengthX else None """

def string_search(text, search):
    dText   = text.split()
    dSearch = search.split()

    found_word = 0

    for text_word in dText:
        for search_word in dSearch:
            if search_word == text_word:
                found_word += 1

    if found_word == len(dSearch):
        return len(dSearch)
    else:
        return None


if __name__ == '__main__':

    """ Get personal data with Polyglot """
    # get files using file_scanner
    files = file_scanner.get_files('/home/vlad/Documents/Repo/python_string-search/path.list')

    for found_file in files: 
        # add found files to DB and compare theyr hashes
        if file_to_db.add_file_to_db(found_file[0], found_file[1]):
            # file is not scanned for personala data
            # read file
            foundNamesCount = 0
            fContent = file_reader.read_file_content(found_file[0], found_file[2])            

            # get Named Entities data (names, surnames)
            text = Text(fContent)
            personalData = ""
            # Start Polyglot-NER timer
            start_time = time.time()
            for entity in text.entities:
                if entity.tag == 'I-PER':
                    foundNamesCount = foundNamesCount + 1 
                    strNames = ' '.join(entity)
                    personalData = personalData + "; " + strNames
            # Stop Polyglot-NER timer
            finish_time = time.time() - start_time
            
            # get personal ID numbers          
            reText = '' . join(text)
            #print("Looking for personal ID's")
            ids = re.findall(r'[2-6][0-9]{10}',reText)
            ids = ' '.join(ids)
            
            # get e-mails
            #print("Looking for emails")
            eMails = re.findall(r'\S+@\S+', reText)
            eMails = ' '.join(eMails)

            # get document number
            #print("Looking for document numbers")
            docNr = re.findall(r'\s[0-9]{8}\s', reText)
            docNr = ' '.join(docNr)
            docNr = docNr.replace("\n", "")
            
            #personalData = personalData + " " + ids + " " + eMails + " " + docNr
            personalData = personalData + " "
            
            # Save data to database
            file_to_db.add_names(found_file[0],personalData)
            file_to_db.set_date(found_file[0])
            print(' ### Found ' + str(foundNamesCount) + ' names in file ' + found_file[0] + '. Took ' + str(finish_time))


    """ BruteForce algorithm test """
    
    """files = file_scanner.get_files('/home/vlad/Documents/Repo/python_string-search/text_sources/')
    
    for found_file in files: 
        fh = open('/home/vlad/Documents/Repo/python_string-search/tmp_text/vardai-pavardes.txt', 'r')
        start_time = time.time()
        foundNamesCount = 0
        fContent = file_reader.read_file_content(found_file[0], found_file[2])
        for line in fh:
            pattern = ''.join(line)
             #print("Looking for word - " + pattern)
            
            f = open('/home/vlad/Documents/Repo/python_string-search/text_sources/wiki-kvant-teorija_2.txt', 'r')
            occ = preprocess(pattern)
            text=f.read()
            
            results = string_search(fContent, pattern)
            if (results != None):
                print(pattern)
                foundNamesCount += 1
        print("File " + found_file[0] + " Brute Force search took --- %s seconds ---" % (time.time() - start_time) + " Found " + str(foundNamesCount))
        fh.close """
    

    """ Boyer Moore algorithm test """
    """files = file_scanner.get_files('/home/vlad/Documents/Repo/python_string-search/text_sources/')
    #fh = open('/home/vlad/Documents/Repo/python_string-search/text_sources/vardai-pavardes.txt', 'r')     
    #start_time = time.time()
    for found_file in files: 
        fh = open('/home/vlad/Documents/Repo/python_string-search/tmp_text/vardai-pavardes.txt', 'r')
        start_time = time.time()
        foundNamesCount = 0
        fContent = file_reader.read_file_content(found_file[0], found_file[2])
        for line in fh:
            pattern = ''.join(line)
            #print("Looking for word - " + pattern)
            
            f = open('text_sources/wiki-straipsnis.txt', 'r')
            text=f.read()
            
            results = boyer_moore_match(fContent, pattern)
            if (results != -1):
                #print(results)
                foundNamesCount += 1
        print("File " + found_file[0] + " Boyer More took --- %s seconds ---" % (time.time() - start_time) + " Found " + str(foundNamesCount))   
        fh.close """
    
    """ Horspool algorithm test """
    """
    fh = open('text_sources/test-list.txt', 'r')
    start_time = time.time()
    for line in fh:
        pattern = ''.join(line)
        print("Looking for word - " + pattern)
        f = open('text_sources/wiki-straipsnis-test.txt', 'r')
        occ = preprocess(pattern)
        text=f.read()
        results = horspool_search(text, pattern, occ)
        print(results)
    print("Horspool search took --- %s seconds ---" % (time.time() - start_time))   
    fh.close""" 

    """ KMP algorithm test """
    """ fh = open('/home/vlad/Documents/Repo/python_string-search/text_sources/vardai-pavardes.txt', 'r')
    start_time = time.time()
    for line in fh:
        pattern = ''.join(line)
        #print("Looking for word - " + pattern)
        f = open('text_sources/wiki-straipsnis.txt', 'r')
        occ = preprocess(pattern)
        text=f.read()
        results = kmp_search(text, pattern)
        if (results != None):
            print(results)
    print("KMP search took --- %s seconds ---" % (time.time() - start_time))
    fh.close """


    """ Suffix tree algorithm test """
    """files = file_scanner.get_files('/home/vlad/Documents/Repo/python_string-search/text_sources/')
    
    
    for found_file in files:
        fh = open('/home/vlad/Documents/Repo/python_string-search/text_sources/vardai-pavardes.txt', 'r')
        start_time = time.time()
        myList =''
        for line in fh:
            myList += ''.join(line)

        myListT = tuple(myList)         
        fContent = file_reader.read_file_content(found_file[0], found_file[2])
            
        result = STree.STree(fContent)
        print(result.find_all(myListT))
        print("File " + found_file[0] + " Suffix Tree search took --- %s seconds ---" % (time.time() - start_time) + " Found ")
        """ 

