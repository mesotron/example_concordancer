# -*- coding: utf-8 -*-

import os
import re
from operator import itemgetter

doc_folder = r"./corpus/"
results_folder = r"./results/"
word_splitter = re.compile(r"\w+")
max_ngram_length = 10

# Loads all documents into memory. Returns a dictionary that maps the documents' 
# filenames to their contents (a list of the lines of the document).
#
def load_docs():
    doc_lines = {}
    doc_sentences = {}
    sentence_splitter = re.compile(r"(.*?)(!|\.|\?)\s")
    
    filenames = os.listdir(doc_folder)
    for filename in filenames:
        doc = open(doc_folder + filename, encoding='utf-8').read().strip() + " "
        doc_lines[filename] = [x.strip() for x in doc.splitlines() if x != '']
        doc_sentences[filename] = ["".join(x) for x in sentence_splitter.findall(doc)]
        doc_sentences[filename].insert(0, doc_lines[filename][0])   # Ensure that first line of document -- the title -- is also at the front of the 'sentences' list, even though it doesn't end in a 
        
    return [doc_lines, doc_sentences]

def create_new_results_file(output_file_prefix):
    i = 1
    filename = ""
    while filename == "" or os.path.exists(filename):
        filename = results_folder + output_file_prefix + str(i) + ".html"
        i += 1
    
    file = open(filename, "w", encoding="utf-8")
    return file


def report_match(search_re, match, line, doc_name, first_in_doc, chapter, results_file):
    if (first_in_doc):
        results_file.write("<h3>" + doc_name + "</h3>")
    
    output = search_re.sub('<b><font color="blue">' + match.group(0) + '</font></b>', line)
    results_file.write("<p>" + chapter + ": " + output)


def get_ngram_at(sent, index, n):
    return " ".join(sent[index : index + n])

def record_ngrams(line, relevant_ngrams, found_ngrams):
    sentence_ngrams = []
    words = word_splitter.findall(line)
    for n in range(1, max_ngram_length + 1):
        for i in range(0, len(words) - n + 1):
            sentence_ngrams.append(get_ngram_at(words, i, n))
            
    for ngram in sentence_ngrams:
        if ngram in relevant_ngrams:
            if ngram in found_ngrams:
                found_ngrams[ngram] += 1
            else:
                found_ngrams[ngram] = 1
    

def search_doc(doc_lines, search_re, use_exclusion_query, exclusion_re, doc_filename, \
               context_results_file, relevant_ngrams, found_ngrams):
    
    doc_name = doc_lines[0].strip() + " (" + doc_filename + ")"
    first_in_doc = True
    chapter = "None"
    chapter_re = re.compile(r"BOOK (\w+)")
    
    for line in doc_lines:
        
        # Update chapter num if necessary
        chaptermatch = chapter_re.search(line)
        if (chaptermatch):
            chapter = chaptermatch.group(1)
        
        # Look for the match we actually care about
        match = search_re.search(line)
        if (match):
            if (not use_exclusion_query) or (not exclusion_re.search(line)):
                
                # Record the context of the match
                report_match(search_re, match, line, doc_name, first_in_doc, chapter, context_results_file)
                first_in_doc = False
                
                # Keep track of any ngrams we find
                record_ngrams(line, relevant_ngrams, found_ngrams)
                


def writeline(line, files):
    for file in files:
        file.write(line + "\n")
        
def load_ngrams(ngram_file):
    ngrams = {}
    with open(ngram_file, 'r', encoding="utf-8") as f:
        for line in f:
            tokens = line.split('\t')
            ngrams[tokens[0]] = int(tokens[1])
    return ngrams

def write_found_ngrams(found_ngrams, freq_results):
    # found_ngrams' keys are ngrams, and values are frequencies.
    # We want to organize these by length, 
    # sort them by frequency,
    # and write them to freq_results.
    
    # Organize by length
    
    found_ngrams_by_length = {}
    for n in range(1, max_ngram_length + 1):
        found_ngrams_by_length[n] = {}
    
    for ngram in found_ngrams:
        length = len(ngram.split(" "))
        found_ngrams_by_length[length][ngram] = found_ngrams[ngram]
    
    # Sort by frequency and write to file
    
    for n in reversed(range(1, max_ngram_length + 1)):
        if found_ngrams_by_length[n]:  # If the dictionary is not empty:
            
            freq_results.write("<h3>Length " + str(n) + "</h3>\n")
            freq_results.write("<table>\n")
            sorted_ngrams = sorted(found_ngrams_by_length[n].items(),key = itemgetter(1),reverse = True)
            
            for ngram, freq in sorted_ngrams:
                if (not (n == 1 and freq == 1)):  # Don't print words that only occur once
                    freq_results.write("<tr><td>" + ngram + "</td><td>" + str(freq) + "</td></tr>\n")    
                    
            freq_results.write("</table>\n")


# all_docs: A dictionary that maps document filenames to the contents of the document.
# docs_to_search: A list of the document filenames to search.
# search_query: The string to search for (using regex formatting)
# use_exclusion_query: Should we use an exclusion query: True or False
# exclusion_query: If we match the search query but we also match the
#                 exclusion query, ignore the match. Ignored if
#                 use_exclusion_query is False.
#
def search_docs(all_docs, docs_to_search, search_query, \
                     use_exclusion_query, exclusion_query, ngram_file):
    
    # Create new files to contain our results; get filenames that
    # don't already exist in results directory
    context_results = create_new_results_file("contexts")
    freq_results = create_new_results_file("frequencies")
    outfiles = [context_results, freq_results]
    writeline("<html><body>", outfiles)
    
    # Load the ngrams we want to consider
    relevant_ngrams = load_ngrams(ngram_file)
    found_ngrams = {}
    
    # Create regular expressions for our search query and exclusion query
    search_re = re.compile(search_query, re.IGNORECASE)
    exclusion_re = re.compile(exclusion_query, re.IGNORECASE)
    
    # Search only those docs that we specified in docs_to_search
    for doc_filename in docs_to_search:
        if (doc_filename in all_docs):
            
            search_doc(all_docs[doc_filename], search_re, \
                        use_exclusion_query, exclusion_re, doc_filename, 
                        context_results, relevant_ngrams, found_ngrams)
        else:
            writeline("<h2>WARNING: " + doc_filename + " not found</h2>", outfiles)
    
    # Collocation finding: make note of any ngrams we found
    write_found_ngrams(found_ngrams, freq_results)
    
    # Close the results files
    writeline("</body></html>", outfiles)
    freq_results.close()
    context_results.close()
    


#################################################
# Specify search parameters here.
#################################################

# 1. Specify documents to search.
# To search all documents, create a list that contains all their filenames,
# like so:
#    docs_to_search = os.listdir(doc_folder)
# To search only the documents in "meditations_1-6.txt", make a list that 
# only contains that document, like so:
#    docs_to_search = ["meditations_1-6.txt"]
    
docs_to_search = os.listdir(doc_folder)

# 2. Specify a search query. Remember that with regular expressions,
# that we put an "r" in front of our strings, and that a vertical 
# bar character | indicates OR. So if we wanted to match the words
# earth OR universe OR cosmos, we could use the following line of code:
#   search_query = r"earth|universe|cosmos"

# If we only want to match these as complete words -- that is, if we
# do NOT want to match earth when it appears inside a larger word like
# "hearth" -- then we have to tell Python to insist on a 'word boundary'
# before and after the word, like so:
#   search_query = r"\b(earth|universe|cosmos)\b"

# Finally, remember that if you want to match special characters like
# full stops, question marks, asterisks, etc., that these have special
# meanings to Python regular expressions and you'll have to 'escape' them
# with a backslash. So to search for three full stops in a row, you'd use:

#   search_query = r"\.\.\."

search_query = r"\b(earth|world|universe|cosmos)\b"

# 3. If use_exclusion_query is True, we will ignore all lines that match
# the exclusion query. The exclusion query is a regular expression, just
# like the search query.

use_exclusion_query = False
exclusion_query = r"dispute"

#################################################

all_doc_lines, all_doc_sentences = load_docs()

search_docs(all_doc_sentences, docs_to_search, search_query, \
             use_exclusion_query, exclusion_query, "meditations_ngrams_2.txt")



print("Done.")
