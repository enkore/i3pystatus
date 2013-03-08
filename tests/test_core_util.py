#!/usr/bin/env python

import unittest
import string
import random
import sys

from i3pystatus.core import util

def get_random_string(length=6, chars=string.printable):
    return ''.join(random.choice(chars) for x in range(length))

def lchop(prefix, string):
    chopped = util.lchop(string, prefix)
    if string.startswith(prefix):
        assert len(chopped) == len(string) - len(prefix)
    if prefix:
        assert not chopped.startswith(prefix)


def lchop_test_generator():
    cases = [
        ('\x0b,S0I', "=t5Bk+\x0b'_;duq=9"),
        ('H1@\x0b_\t', '<&9<;Q(0L";^$7'),
        ('NWV#B0u', '~Q_wx5"$W\x0b[(T'),
        ('by=uHfZ>', 'AdytjC5-OUR\\'),
        ('/FD|^6=m3', 'l0:%ibW7*}S'),
        ('!.LsV90/$\x0b', 'nD}L&4]MGC'),
        ('S0zOIvbm:~L', 'jJ\\UGOMY<'),
        ("'aZ@,AA\x0b;Dmm", 'ZD +9}f;'),
        ('Ae;=SoHD(1VPJ', 'x\r)du,+'),
        ('ANDT \t>tZ1Iy9}', 'wpz%F`'),
        ('|w?>bv,t# BkGeE', '07mZR'),
        ('1MSN\x0c\r}Tu8r3uCe)', '\\I6-'),
        ('0;-!MVW4+\rz]J3@SQ', 'lvG'),
        ('Zi\x0b^5E?}a\\KJ(,O4n(', '8:'),
        ('I-X[~2sQigGLA_~ZD%G', '#'),
        (':xio!', 'v=ApOu\t_,}'),
        ('%bM%W\n', '7$wZ]gaL!U/%'),
        ('~\x0bILq>+', '[4}LhQ1zz1m?D&'),
        ('+"a)\x0c:4Q', '\niNQ+GY8+)UtQ\r#M'),
        ('R3PHi/[S*', 'J7fV19X(c^^J(9BAY+'),
        ('%Z?=m|3Wtr', 'O7K%GpQRJR%y}wIDq~H\\'),
        ('wyR0V*y^+D)', '>tsX)@%=u[83/hf0j?+xXV'),
        ('4}joZKr?j$u)', '\r\x0cje4QAha\\Y2]V\n`5[.TG~$0'),
        ('at%Y)%g5.*vKJ', 'MnucPcE!h;gkhAdI*`Jv$%dafJ'),
        ('XKH\\n\'gf4@"6`-', '#~:Nt[^9wtE.4\\@<i|tWiu|p7:uw'),
        ('mLV!q;:\n\nk5u\x0cD>', "9)#qPuEF-A@ -DTE\r= (KgM\\h'i$XU"),
        ("<|(h|P9Wz9d9'u,M", '7d-A\nY{}5"\' !*gHHh`x0!B2Ox?yeKb\x0b'),
        ('bV?:f\x0b#HDhuwSvys3', ";\r,L![\x0cU7@ne@'?[*&V<dap]+Tq[n1!|PE"),
        ('T\r~bGV^@JC?P@Pa66.', "9,q>VI,[}pHM\nB65@LfE16VJPw=r'zU\x0bzWj@"),
        ('^|j7N!mV0o(?*1>p?dy', '\\ZdA&:\t\x0b:8\t|7.Kl,oHw-\x0cS\nwZlND~uC@le`Sm'),
    ]
    for prefix, string in cases:
        yield lchop, prefix, prefix+string
        yield lchop, prefix, string
        yield lchop, string, string
        yield lchop, string, prefix
        yield lchop, "", string
        yield lchop, prefix, ""

def partition(iterable, limit, assrt):
    partitions = util.partition(iterable, limit)
    partitions = [sorted(partition) for partition in partitions]
    for item in assrt:
        assert sorted(item) in partitions


def partition_test_generator():
    cases = [
        ([1, 2, 3, 4], 3, [[1,2], [3], [4]]),
        ([2, 1, 3, 4], 3, [[1,2], [3], [4]]),
        ([0.33, 0.45, 0.89], 1, [[0.33, 0.45, 0.89]]),
        ([], 10, []),
    ]

    for iterable, limit, assrt in cases:
        yield partition, iterable, limit, assrt

def popwhile(iterable, predicate, assrt):
    assert list(util.popwhile(predicate, iterable)) == assrt

def popwhile_test_generator():
    cases = [
        ([1, 2, 3, 4], lambda x: x < 2, []),
        ([1, 2, 3, 4], lambda x: x < 5 and x > 2, [4, 3]),
        ([1, 2, 3, 4], lambda x: x == 4, [4]),
        ([1, 2, 3, 4], lambda x: True, [4, 3, 2, 1]),
        ([1, 2], lambda x: False, []),
    ]

    for iterable, predicate, assrt in cases:
        yield popwhile, iterable, predicate, assrt
