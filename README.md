# Impose

A simple script for book [imposition](https://en.wikipedia.org/wiki/Imposition).
Given a PDF, the script will shuffle the pages into a correct order so the book
can be printed on double sided paper, and the paper folded to form a book.

## Requirements

As normal with python script, create a virtual environment and install
the required modules, pypdf and argparse:

```
python3 -m venv venv
. venv/bin/activate
python -m pip install -r requirements.txt
```

## Possible usage

Save the book as a PDF file. Enusure there are no intenral links, for example
index or contents pages, as this will cause the pypdf library to crash. Save the
file as `input.pdf` Run:
```
python unfold.py
```
against that pdf file to create a new PDF which is paginated correctly into 
`imposed.pdf`.
Once printed two sided the pages can be folded into sections.

## TODO

This is in a fairly early phase of development. The PDF filenames and the number of
folds are hard-coded.