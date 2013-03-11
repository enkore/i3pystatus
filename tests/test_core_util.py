#!/usr/bin/env python

import unittest
from unittest.mock import MagicMock
import string
import random
import sys
import types

from i3pystatus.core import util

def get_random_string(length=6, chars=string.printable):
    return ''.join(random.choice(chars) for x in range(length))

def lchop(prefix, string):
    chopped = util.lchop(string, prefix)
    if string.startswith(prefix):
        assert len(chopped) == len(string) - len(prefix)
    assert not (prefix and chopped.startswith(prefix))

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
        yield lchop, prefix+prefix, prefix+prefix+prefix+string

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

def keyconstraintdict_missing(valid, required, feedkeys, assrt_missing):
    kcd = util.KeyConstraintDict(valid_keys=valid, required_keys=required)
    kcd.update(dict.fromkeys(feedkeys))

    assert kcd.missing() == set(assrt_missing)

def keyconstraintdict_missing_test_generator():
    cases = [
        # ( valid,              required, feed,      missing )
        (("foo", "bar", "baz"), ("foo",), ("bar",), ("foo",)),
        (("foo", "bar", "baz"), ("foo",), tuple(), ("foo",)),
        (("foo", "bar", "baz"), ("bar", "baz"), ("bar", "baz"), tuple()),
        (("foo", "bar", "baz"), ("bar", "baz"), ("bar", "foo", "baz"), tuple()),
    ]

    for valid, required, feed, missing in cases:
        yield keyconstraintdict_missing, valid, required, feed, missing

class ModuleListTests(unittest.TestCase):
    class ModuleBase:
        pass

    def setUp(self):
        self.status_handler = MagicMock()
        self.ml = util.ModuleList(self.status_handler, self.ModuleBase)

    def test_append_simple(self):
        module = self.ModuleBase()
        module.registered = MagicMock()

        self.ml.append(module)
        module.registered.assert_called_with(self.status_handler)

    def _create_module_class(self, name, bases=None):
        if not bases: bases = (self.ModuleBase,)
        return type(name, bases, {
            "registered": MagicMock(),
            "__init__": MagicMock(return_value=None),
        })

    def test_append_class_instanciation(self):
        module_class = self._create_module_class("module_class")

        self.ml.append(module_class)

        module_class.__init__.assert_called_with()
        module_class.registered.assert_called_with(self.status_handler)

    def test_append_module(self):
        pymod = types.ModuleType("test_mod")
        pymod.some_class = self._create_module_class("some_class")
        pymod.some_class.__module__ = "test_mod"

        self.ml.append(pymod)

        pymod.some_class.__init__.assert_called_with()
        pymod.some_class.registered.assert_called_with(self.status_handler)

    def test_append_module2(self):
        # Here we test if imported classes are ignored as they should
        pymod = types.ModuleType("test_mod")
        pymod.some_class = self._create_module_class("some_class")
        pymod.some_class.__module__ = "other_module"

        with self.assertRaises(IndexError):
            self.ml.append(pymod)

        assert not pymod.some_class.__init__.called
        assert not pymod.some_class.registered.called

    def test_append_class_inheritance(self):
        in_between = self._create_module_class("in_between")
        cls = self._create_module_class("cls", (in_between,))

        self.ml.append(cls)

        cls.__init__.assert_called_with()
        cls.registered.assert_called_with(self.status_handler)

class PrefixedKeyDictTests(unittest.TestCase):
    def test_no_prefix(self):
        dict = util.PrefixedKeyDict("")
        dict["foo"] = None
        dict["bar"] = 42

        assert dict["foo"] == None
        assert dict["bar"] == 42

    def test_prefix(self):
        dict = util.PrefixedKeyDict("pfx_")
        dict["foo"] = None
        dict["bar"] = 42

        assert dict["pfx_foo"] == None
        assert dict["pfx_bar"] == 42

    def test_dict(self):
        d = util.PrefixedKeyDict("pfx_")
        d["foo"] = None
        d["bar"] = 42

        realdict = dict(d)

        assert realdict["pfx_foo"] == None
        assert realdict["pfx_bar"] == 42

class KeyConstraintDictAdvancedTests(unittest.TestCase):
    def test_invalid_1(self):
        kcd = util.KeyConstraintDict(valid_keys=tuple(), required_keys=tuple())
        with self.assertRaises(KeyError):
            kcd["invalid"] = True

    def test_invalid_2(self):
        kcd = util.KeyConstraintDict(valid_keys=("foo", "bar"), required_keys=tuple())
        with self.assertRaises(KeyError):
            kcd["invalid"] = True

    def test_incomplete_iteration(self):
        kcd = util.KeyConstraintDict(valid_keys=("foo", "bar"), required_keys=("foo",))
        with self.assertRaises(util.KeyConstraintDict.MissingKeys):
            for x in kcd:
                pass

    def test_completeness(self):
        kcd = util.KeyConstraintDict(valid_keys=("foo", "bar"), required_keys=("foo",))
        kcd["foo"] = False
        for x in kcd:
            pass
        assert kcd.missing() == set()

    def test_remove_required(self):
        kcd = util.KeyConstraintDict(valid_keys=("foo", "bar"), required_keys=("foo",))
        kcd["foo"] = None
        assert kcd.missing() == set()
        del kcd["foo"]
        assert kcd.missing() == set(["foo"])

    def test_set_twice(self):
        kcd = util.KeyConstraintDict(valid_keys=("foo", "bar"), required_keys=("foo",))
        kcd["foo"] = 1
        kcd["foo"] = 2
        assert kcd.missing() == set()
        del kcd["foo"]
        assert kcd.missing() == set(["foo"])
