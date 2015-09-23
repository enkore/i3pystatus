#!/usr/bin/env python

import unittest
from unittest.mock import MagicMock
import string
import random
import types

import pytest

from i3pystatus.core.exceptions import ConfigAmbigiousClassesError, ConfigInvalidModuleError
from i3pystatus.core import util, ClassFinder


def test_lchop_prefixed():
    assert util.lchop("12345", "12") == "345"


def test_lchop_no_prefix():
    assert util.lchop("345", "") == "345"


def test_lchop_unmatched():
    assert util.lchop("12345", "345") == "12345"


@pytest.mark.parametrize("iterable, limit, assrt", [
    ([1, 2, 3, 4], 3, [[1, 2], [3], [4]]),
    ([2, 1, 3, 4], 3, [[1, 2], [3], [4]]),
    ([0.33, 0.45, 0.89], 1, [[0.33, 0.45, 0.89]]),
    ([], 10, []),
])
def test_partition(iterable, limit, assrt):
    partitions = util.partition(iterable, limit)
    partitions = [sorted(partition) for partition in partitions]
    for item in assrt:
        assert sorted(item) in partitions


@pytest.mark.parametrize("iterable, predicate, assrt", [
    ([1, 2, 3, 4], lambda x: x < 2, []),
    ([1, 2, 3, 4], lambda x: x < 5 and x > 2, [4, 3]),
    ([1, 2, 3, 4], lambda x: x == 4, [4]),
    ([1, 2, 3, 4], lambda x: True, [4, 3, 2, 1]),
    ([1, 2], lambda x: False, []),
])
def test_popwhile(iterable, predicate, assrt):
    assert list(util.popwhile(predicate, iterable)) == assrt


@pytest.mark.parametrize("valid, required, feed, missing", [
    # ( valid,              required, feed,      missing )
    (("foo", "bar", "baz"), ("foo",), ("bar",), ("foo",)),
    (("foo", "bar", "baz"), ("foo",), tuple(), ("foo",)),
    (("foo", "bar", "baz"), ("bar", "baz"), ("bar", "baz"), tuple()),
    (("foo", "bar", "baz"), ("bar", "baz"), ("bar", "foo", "baz"), tuple()),

])
def test_keyconstraintdict_missing(valid, required, feed, missing):
    kcd = util.KeyConstraintDict(valid_keys=valid, required_keys=required)
    kcd.update(dict.fromkeys(feed))

    assert kcd.missing() == set(missing)


class ModuleListTests(unittest.TestCase):
    class ModuleBase:
        pass

    def setUp(self):
        self.status_handler = MagicMock()
        self.ml = util.ModuleList(self.status_handler, ClassFinder(self.ModuleBase))

    def test_append_simple(self):
        module = self.ModuleBase()
        module.registered = MagicMock()

        self.ml.append(module)
        module.registered.assert_called_with(self.status_handler)

    def _create_module_class(self, name, bases=None):
        if not bases:
            bases = (self.ModuleBase,)
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

        with self.assertRaises(ConfigInvalidModuleError):
            self.ml.append(pymod)

        assert not pymod.some_class.__init__.called
        assert not pymod.some_class.registered.called

    def test_ambigious_classdef(self):
        pymod = types.ModuleType("test_mod")
        pymod.some_class = self._create_module_class("some_class")
        pymod.some_class.__module__ = "test_mod"
        pymod.some_other_class = self._create_module_class("some_other_class")
        pymod.some_other_class.__module__ = "test_mod"

        with self.assertRaises(ConfigAmbigiousClassesError):
            self.ml.append(pymod)

    def test_invalid_module(self):
        pymod = types.ModuleType("test_mod")

        with self.assertRaises(ConfigInvalidModuleError):
            self.ml.append(pymod)

    def test_append_class_inheritance(self):
        in_between = self._create_module_class("in_between")
        cls = self._create_module_class("cls", (in_between,))

        self.ml.append(cls)

        cls.__init__.assert_called_with()
        cls.registered.assert_called_with(self.status_handler)


class KeyConstraintDictAdvancedTests(unittest.TestCase):
    def test_invalid_1(self):
        kcd = util.KeyConstraintDict(valid_keys=tuple(), required_keys=tuple())
        with self.assertRaises(KeyError):
            kcd["invalid"] = True

    def test_invalid_2(self):
        kcd = util.KeyConstraintDict(
            valid_keys=("foo", "bar"), required_keys=tuple())
        with self.assertRaises(KeyError):
            kcd["invalid"] = True

    def test_incomplete_iteration(self):
        kcd = util.KeyConstraintDict(
            valid_keys=("foo", "bar"), required_keys=("foo",))
        with self.assertRaises(util.KeyConstraintDict.MissingKeys):
            for x in kcd:
                pass

    def test_completeness(self):
        kcd = util.KeyConstraintDict(
            valid_keys=("foo", "bar"), required_keys=("foo",))
        kcd["foo"] = False
        for x in kcd:
            pass
        assert kcd.missing() == set()

    def test_remove_required(self):
        kcd = util.KeyConstraintDict(
            valid_keys=("foo", "bar"), required_keys=("foo",))
        kcd["foo"] = None
        assert kcd.missing() == set()
        del kcd["foo"]
        assert kcd.missing() == {"foo"}

    def test_set_twice(self):
        kcd = util.KeyConstraintDict(
            valid_keys=("foo", "bar"), required_keys=("foo",))
        kcd["foo"] = 1
        kcd["foo"] = 2
        assert kcd.missing() == set()
        del kcd["foo"]
        assert kcd.missing() == {"foo"}


class FormatPTests(unittest.TestCase):
    def test_escaping(self):
        assert util.formatp("[razamba \[ mabe \]]") == "razamba [ mabe ]"

    def test_numerical(self):
        assert util.formatp("[{t} - [schmuh {x}]]", t=1, x=2) == "1 - schmuh 2"
        assert util.formatp("[{t} - [schmuh {x}]]", t=1, x=0) == "1 - "
        assert util.formatp("[{t} - [schmuh {x}]]", t=0, x=0) == ""

    def test_nesting(self):
        s = "[[{artist} - ]{album} - ]{title}"
        assert util.formatp(s, title="Black rose") == "Black rose"
        assert util.formatp(
            s, artist="In Flames", title="Gyroscope") == "Gyroscope"
        assert util.formatp(
            s, artist="SOAD", album="Toxicity", title="Science") == "SOAD - Toxicity - Science"
        assert util.formatp(
            s, album="Toxicity", title="Science") == "Toxicity - Science"

    def test_bare(self):
        assert util.formatp("{foo} blar", foo="bar") == "bar blar"

    def test_presuffix(self):
        assert util.formatp(
            "ALINA[{title} schnacke]KOMMAHER", title="") == "ALINAKOMMAHER"
        assert util.formatp("grml[{title}]") == "grml"
        assert util.formatp("[{t}]grml") == "grml"

    def test_side_by_side(self):
        s = "{status} [{artist} / [{album} / ]]{title}[ {song_elapsed}/{song_length}]"
        assert util.formatp(s, status="▷", title="Only For The Weak",
                            song_elapsed="1:41", song_length="4:55") == "▷ Only For The Weak 1:41/4:55"
        assert util.formatp(
            s, status="", album="Foo", title="Die, Die, Crucified", song_elapsed="2:52") == " Die, Die, Crucified"
        assert util.formatp("[[{a}][{b}]]", b=1) == "1"

    def test_complex_field(self):
        class NS:
            pass
        obj = NS()
        obj.attr = "bar"

        s = "[{a:.3f} m]{obj.attr}"
        assert util.formatp(s, a=3.14123456789, obj=obj) == "3.141 mbar"
        assert util.formatp(s, a=0.0, obj=obj) == "bar"
