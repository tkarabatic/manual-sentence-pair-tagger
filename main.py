import os
import re
from dotenv import dotenv_values
from tkinter import Button, Checkbutton, Frame, IntVar, Label, LEFT, Tk

from helpers import (
    get_grouped_sentences,
    get_processed_data,
    get_unprocessed_sentence_data,
    write_to_file
)

config = dotenv_values('.env')

PROCESSED_SENTENCE_FILENAME = config['PROCESSED_SENTENCE_FILENAME']
SELECTED_PAIRS_FILENAME = config['SELECTED_PAIRS_FILENAME']
# Note: the rows must be sorted alphabetically for the grouping script to work.
SENTENCE_SOURCE_FILENAME = config['SENTENCE_SOURCE_FILENAME']


class SentenceMatcher:
    def __init__(
        self, window, save_handler, exit_handler, sentences, past_keywords
    ):
        self.window = window
        window.title("Sentence Matcher")
        window.bind('<Escape>', lambda event: exit_handler())

        # labels
        self.lbl_status = Label(self.window)
        self.lbl_status.grid(row=0, column=0, pady=10)
        self.lbl_keyword = None

        # handlers
        self.save_handler = save_handler
        self.exit_handler = exit_handler

        # sentences and keywords
        self.sentences = sentences
        self.current_sentence = None
        # the index starts at -1 because it is incremented before loading the
        # sentence
        self.current_sentence_index = -1
        self.selected_keywords = list()
        self.past_keywords = list(past_keywords)
        self.selected_matches = list()

        # destroyable window elements
        self.current_sentence_keyword_elements = list()
        self.candidate_elements = list()

        if len(self.sentences):
            self.__load_current_sentence()

        self.control_btn_container = None
        self.__draw_control_buttons()

    def __add_window_element(self, element, is_keyword=True):
        elements = (self.current_sentence_keyword_elements if is_keyword
                    else self.candidate_elements)
        elements.append(element)

    def __clear_window_elements(self, is_keyword=True):
        elements = (self.current_sentence_keyword_elements if is_keyword
                    else self.candidate_elements)
        for element in elements:
            element.destroy()
        elements.clear()

    def __set_keyword_label(self):
        if not self.current_sentence:
            if self.lbl_keyword:
                self.lbl_keyword.destroy()
                self.lbl_keyword = None
                return
        text = (', '.join(self.selected_keywords)
                if len(self.selected_keywords) else 'None')
        if self.lbl_keyword is None:
            self.lbl_keyword = Label(self.window)
            self.lbl_keyword.grid(row=2, column=0, pady=10)
        self.lbl_keyword['text'] = 'Selected keywords: %s' % text

    def __contains_selected_keywords(self, text):
        if not len(self.selected_keywords):
            return False

        matches_all_keywords = True
        for k in self.selected_keywords:
            if not re.search(k, text, re.IGNORECASE):
                matches_all_keywords = False
                break
        return matches_all_keywords

    def __highlight_window_elements(self):
        elements = (self.current_sentence_keyword_elements
                    + self.candidate_elements)
        for element in elements:
            is_keyword_button = isinstance(element, Button)
            is_candidate_check = isinstance(element, Checkbutton)
            if not (is_keyword_button or is_candidate_check):
                continue
            is_highlighted = False
            if len(self.selected_keywords):
                if is_keyword_button:
                    is_highlighted = element['text'] in self.selected_keywords
                else:
                    text = element['text']
                    is_highlighted = self.__contains_selected_keywords(text)
            element['fg'] = ('black'
                             if not is_highlighted or not is_keyword_button
                             else 'white')
            element['bg'] = ('medium sea green' if is_highlighted
                             else 'white' if is_keyword_button else 'gray95')

    def __get_toggle_fn(self, value, is_keyword=True):
        def handler():
            fn = (self.__toggle_keyword_selection
                  if is_keyword else self.__toggle_match_selection)
            fn(value)
        return handler

    def __draw_sentence_keywords(self):
        self.__clear_window_elements()
        if not self.current_sentence:
            return
        f1 = Frame(self.window)
        f1.grid(row=1, column=0)
        idx_lbl = Label(f1, text='%d/%d' % (
            self.current_sentence_index + 1, len(self.sentences)))
        idx_lbl.pack(side=LEFT)
        self.__add_window_element(idx_lbl)
        for word in self.current_sentence['keywords']:
            btn_keyword = Button(f1, text=word,
                                 command=self.__get_toggle_fn(word))
            btn_keyword.pack(side=LEFT)
            self.__add_window_element(btn_keyword)
        self.__add_window_element(f1)

    def __draw_candidate_sentences(self):
        self.__clear_window_elements(False)
        if not self.current_sentence:
            return
        sorted_candidates = self.current_sentence['candidates']
        # a candidate sentence should be displayed at the top if it contains
        # all the selected keywords or it has been selected (regardless of
        # whether it contains the keywords)
        if len(self.selected_keywords):
            sorted_candidates = sorted(
                sorted_candidates,
                key=lambda c: (c in self.selected_matches
                               or self.__contains_selected_keywords(c)),
                reverse=True)

        f2 = Frame(self.window)
        f2.grid(row=3, column=0, sticky='W', padx=50, pady=5)

        for index, sentence in enumerate(sorted_candidates):
            is_checked = 1 if sentence in self.selected_matches else 0
            check_val = IntVar(value=is_checked)
            chk = Checkbutton(f2, text=sentence, variable=check_val,
                              command=self.__get_toggle_fn(sentence, False))
            chk.grid(row=index, column=0, sticky='w')
            # save the ref to stop the variable from being garbage collected
            chk.check_val = check_val
            self.__add_window_element(chk, False)
        self.__add_window_element(f2, False)

    def __set_status_label(self):
        status_text = ('Select a keyword to filter by:'
                       if self.current_sentence else 'No sentence to display.')
        if self.lbl_status['text'] != status_text:
            self.lbl_status['text'] = status_text

    def __draw_control_buttons(self):
        self.__set_status_label()

        if self.control_btn_container:
            self.control_btn_container.destroy()

        btn_container = Frame(self.window)
        self.control_btn_container = btn_container
        btn_container.grid(row=4, column=0, pady=10)
        save_state = 'normal' if self.current_sentence else 'disabled'
        btn_save = Button(btn_container, text='Save', command=self.__save,
                          state=save_state)
        btn_save.grid(row=0, column=0, padx=30)
        btn_save.bind('<Return>', lambda event: self.__save())

        self.control_btn_container.btn_save = btn_save
        btn_exit = Button(btn_container, text='Exit',
                          command=self.exit_handler)
        btn_exit.bind('<Return>', lambda event: self.exit_handler())
        btn_exit.grid(row=0, column=1, padx=30)
        self.control_btn_container.btn_exit = btn_exit
        focused_button = btn_save if self.current_sentence else btn_exit
        focused_button.focus()

    def __load_current_sentence(self):
        new_index = self.current_sentence_index + 1
        self.current_sentence = (self.sentences[new_index]
                                 if new_index < len(self.sentences) else None)
        self.current_sentence_index = new_index
        self.selected_keywords = list()
        if self.current_sentence:
            print('LOADING SENTENCE #%d' % (new_index + 1))
            matching_keywords = [k for k in self.past_keywords
                                 if k in self.current_sentence['keywords']]
            self.selected_matches = list()
            if len(matching_keywords):
                self.selected_keywords.extend(matching_keywords)
                keywords = ', '.join(matching_keywords)
                print('-> preselected keywords: %s' % keywords)
        else:
            self.__draw_control_buttons()
        self.__set_status_label()
        self.__set_keyword_label()
        self.__draw_sentence_keywords()
        self.__draw_candidate_sentences()
        self.__highlight_window_elements()

    def __toggle_keyword_selection(self, keyword):
        if keyword in self.selected_keywords:
            self.selected_keywords.remove(keyword)
        else:
            self.selected_keywords.append(keyword)
        self.__set_keyword_label()
        self.__draw_candidate_sentences()
        self.__highlight_window_elements()

    def __toggle_match_selection(self, candidate):
        if candidate in self.selected_matches:
            self.selected_matches.remove(candidate)
        else:
            self.selected_matches.append(candidate)
        print('selected matches: %s' % ', '.join(self.selected_matches))

    def __save(self):
        if not self.current_sentence:
            return
        if len(self.selected_keywords):
            for keyword in self.selected_keywords:
                if keyword not in self.past_keywords:
                    self.past_keywords.append(keyword)
        self.save_handler(self.current_sentence['sentence'],
                          self.selected_keywords, self.selected_matches)
        self.__load_current_sentence()


def save_sentence_data(sentence, keywords, matches):
    print('SAVING...')
    print('-> sentence: %s' % sentence)
    processed_data = '%s,%s' % (sentence, '|'.join(keywords))
    write_to_file([processed_data], PROCESSED_SENTENCE_FILENAME, 'a')
    print('-> keywords: %s' % keywords)
    if len(matches):
        items = ['%s,%s,1' % (sentence, match) for match in matches]
        write_to_file(items, SELECTED_PAIRS_FILENAME, 'a')
    print('-> matches: %s' % matches)


def main():
    root = Tk()

    grouped = get_grouped_sentences(SENTENCE_SOURCE_FILENAME)
    processed_sentences, processed_keywords = get_processed_data(
        PROCESSED_SENTENCE_FILENAME)
    unprocessed = get_unprocessed_sentence_data(grouped, processed_sentences)
    print('past keywords: %s' % ', '.join(sorted(processed_keywords)))
    print('unrated sentences: %d' % len(unprocessed))

    SentenceMatcher(root, save_sentence_data, root.destroy, unprocessed,
                    processed_keywords)

    root.mainloop()


if __name__ == '__main__':
    main()
