# Standard library
import ast
from os.path import basename

def dotted_getattr(obj, attribute):
    attributes = attribute.split('.')
    for attr in attributes:
        obj = getattr(obj, attr)

    return obj


def is_public(node):
    return not node.name.startswith('_')


def is_py_file(filename):
    return filename.endswith('.py')


def parse_file(path):
    with open(path) as f:
        source = f.read()
    return ast.parse(source, basename(path))
