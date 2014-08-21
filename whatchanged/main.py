#!/usr/bin/env python

from __future__ import absolute_import, print_function

# Standard library
from os import walk
from os.path import exists, isdir, join

# Local library
from .util import is_py_file
from .diff import diff_files


def main():
    import sys

    if len(sys.argv) < 3:
        print('Usage: %s <package1/module1> <package2/module2>' % sys.argv[0])
        sys.exit(1)

    old, new = sys.argv[1:3]

    diff = set([])

    if isdir(old):
        assert isdir(new)
        for dirpath, dirnames, filenames in walk(new):
            for file_ in filenames:
                if is_py_file(file_):
                    new_file = join(dirpath, file_)
                    old_file = new_file.replace(new, old)
                    if exists(old_file):
                        mdiff = diff_files(old_file, new_file)
                        if mdiff is not None:
                            diff.add(mdiff)

    else:
        diff.add(diff_files(old, new))

    for module in diff:
        print(module)

if __name__ == '__main__':
    main()
