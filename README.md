# Manual sentence pair tagger
[![PEP8](https://img.shields.io/badge/code%20style-pep8-orange.svg)](https://www.python.org/dev/peps/pep-0008/)

A simple `tkinter` app that reads sentence pairs from a `.csv` file and allows
the user to tag matching sentences within each group (with optional keyword
filtering).

It outputs two `.csv` files: one containing the selected sentence pairs, and
the other recording the keyword selections per sentence.

**Note:** The rows in the sentence source file must be sorted alphabetically
for the grouping script to work.
