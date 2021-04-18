import csv
import os
import string


def get_path(filename):
    CURRENT_FOLDER = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(CURRENT_FOLDER, filename)


def yield_csv_rows(filename):
    with open(get_path(filename), newline='\n') as file:
        reader = csv.reader(file, delimiter=',')
        for row in reader:
            yield([row[0], row[1]])


def write_to_file(items, filename, mode='w'):
    file = open(get_path(filename), mode)
    for it in items:
        file.write('%s\n' % (it))
    file.close()


# file row format: sentence_1,sentence_2
# [no initial .csv header row]
def get_grouped_sentences(filename):
    groups = list()
    current_group = list()
    for sentence_1, sentence_2 in yield_csv_rows(filename):
        if len(current_group) == 0:
            current_group.append(sentence_1)
        elif current_group[0] != sentence_1:
            groups.append(list(current_group))
            current_group = list()
            current_group.append(sentence_1)
        current_group.append(sentence_2)
    return groups


# file row format: sentence,keyword_1|keyword_2|...
# [no initial .csv header row]
def get_processed_data(filename):
    sentences = list()
    keywords = list()
    for sentence, selected_keywords in yield_csv_rows(filename):
        sentences.append(sentence)
        keyword_values = selected_keywords.split('|')
        for k in keyword_values:
            if k and k not in keywords:
                keywords.append(k)
    return sentences, keywords


def get_sentence_data(items):
    sentence = items[0]
    # extract keywords from the sentence to facilitate searches; keep the
    # apostrophes to preserve the Saxon genitive
    punctuation = string.punctuation.replace("'", '')
    words = sentence.translate(str.maketrans('', '', punctuation)).split(' ')
    return {'sentence': sentence, 'keywords': words, 'candidates': items[1:]}


def get_unprocessed_sentence_data(grouped, processed):
    unprocessed = [g for g in grouped if g[0] not in processed]
    return [get_sentence_data(i) for i in unprocessed]
