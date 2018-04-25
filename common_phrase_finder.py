# -*- coding: utf-8 -*-

import os
import re
from operator import itemgetter  

doc_folder = r"./corpus/"
output_file_prefix = "meditations"
min_count = 2       # Minimum frequency of phrase to be worth keeping track of
max_n = 10          # Maximum phrase length

# Loads all documents into memory. Returns a dictionary that maps the documents' 
# filenames to their contents (a list of the lines of the document).
#
def load_docs():
    doc_sentences = {}
    doc_words = {}
    sentence_splitter = re.compile(r"(.*?)(!|\.|\?)\s")
    word_splitter = re.compile(r"\w+")
    
    filenames = os.listdir(doc_folder)
    for filename in filenames:
        doc = open(doc_folder + filename, encoding='utf-8').read().strip() + " "
        doc_sentences[filename] = [x[0].lower() + x[1] for x in sentence_splitter.findall(doc)]
        doc_words[filename] = [word_splitter.findall(sent) for sent in doc_sentences[filename]]
        
    return doc_words

def get_ngram_at(sent, index, n):
    return " ".join(sent[index : index + n])

def get_ngrams(all_ngrams, all_doc_words, n):
    ngram = ""
    all_ngrams[n] = {}
    shorter_ngrams = None
    if (n > 1):
        shorter_ngrams = all_ngrams[n - 1]
    
    for filename in all_doc_words:
        for sent in all_doc_words[filename]:
            for i in range(0, len(sent) - n + 1):
                if n > 1:
                    ngram = get_ngram_at(sent, i, n - 1)
                    
                if (n == 1 or ngram in shorter_ngrams):
                    ngram = get_ngram_at(sent, i, n)
                    if (ngram in all_ngrams[n]):
                        all_ngrams[n][ngram] += 1
                    else:
                        all_ngrams[n][ngram] = 1
    
    print("Winnowing " + str(n) + "-grams...")
    for ngram in list(all_ngrams[n]):
        if all_ngrams[n][ngram] < min_count:
            del all_ngrams[n][ngram]
            
    return all_ngrams

def write_ngrams(output_filename, all_ngrams):
    with open(output_filename, 'w', encoding="utf-8") as f:
        for n in range(1, max_n + 1):
            
            sorted_ngrams = sorted(all_ngrams[n].items(),key = itemgetter(1),reverse = True)
            for ngram, freq in sorted_ngrams:
                f.write(ngram + "\t" + str(freq) + "\n")

all_doc_words = load_docs()
all_ngrams = {}  # maps phrase length 'n' to an ngram frequency dictionary

for n in range(1, max_n + 1):
    all_ngrams = get_ngrams(all_ngrams, all_doc_words, n)


write_ngrams(output_file_prefix + "_ngrams_" + str(min_count) + ".txt", all_ngrams)
print("Done.")







