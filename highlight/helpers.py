# helpers.py

import os
import re


def dbg(string):
    print(f"------------------------------ {string}")


def p(string=""):
    print(string)


def error(string):
    print(f"\n ERROR: {string}")


def make_abs_path_to_script_dir(rel_path):
    script_dir = os.path.dirname(__file__)
    return os.path.normpath(os.path.join(script_dir, rel_path))



def sanitize_filename(filename):
    return re.sub(r'(?u)[^-\w.{}]', '', filename.strip())


from .ext_highlights import working_dir

def make_abs_path_rel_to_working_dir(rel_path):
    return os.path.normpath(os.path.join(working_dir, rel_path))



def asc(a, b):
    return min(a, b), max(a, b)
