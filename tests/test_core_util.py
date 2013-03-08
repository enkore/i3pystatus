#!/usr/bin/env python

import unittest
import string
import random
import sys

from i3pystatus.core import util

def get_random_string(length=6, chars=string.printable):
    return ''.join(random.choice(chars) for x in range(length))

def lchop_factory(prefix, string):
    def test():
        chopped = util.lchop(string, prefix)
        if string.startswith(prefix):
            assert len(chopped) == len(string) - len(prefix)
        if prefix:
            assert not chopped.startswith(prefix)
    test.description = "lchop_test:prefix={}:string={}".format(prefix, string)
    return test

def lchop_test_generator():
    nmin = 5
    nmax = 20
    for n in range(nmin, nmax):
        prefix = get_random_string(n)
        string = get_random_string(2*nmax-n)
        yield lchop_factory(prefix, prefix+string)
        yield lchop_factory(prefix, string)
        yield lchop_factory(string, string)
        yield lchop_factory(string, prefix)
        yield lchop_factory("", string)


def partition_factory(iterable, limit, assrt):
    def test():
        partitions = util.partition(iterable, limit)
        partitions = [sorted(partition) for partition in partitions]
        for item in assrt:
            assert sorted(item) in partitions
    test.description = "partition_test:iterable={}:limit={}:expected={}".format(iterable, limit, assrt)
    return test

def partition_test_generator():
    cases = [
        ([1, 2, 3, 4], 3, [[1,2], [3], [4]]),
        ([2, 1, 3, 4], 3, [[1,2], [3], [4]]),
        ([0.33, 0.45, 0.89], 1, [[0.33, 0.45, 0.89]]),
        ([], 10, []),
    ]

    for iterable, limit, assrt in cases:
        yield partition_factory(iterable, limit, assrt)

suite = unittest.TestLoader().loadTestsFromName(__name__)
unittest.TextTestRunner(verbosity=2).run(suite)
