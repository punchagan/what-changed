# 3rd-party library
from astroid.builder import AstroidBuilder

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
    return AstroidBuilder().file_build(path)

def parse_string(code):
    return AstroidBuilder().string_build(code)
