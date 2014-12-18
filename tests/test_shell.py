#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging

from i3pystatus.shell import Shell
from i3pystatus.core.command import run_through_shell


class ShellModuleMetaTest(unittest.TestCase):

    valid_output = "hello world"

    def test_shell_correct_output(self):
        # ShellTest test
        # http://python.readthedocs.org/en/latest/library/unittest.html
        retcode, out, err = run_through_shell("echo '%s'" % (self.valid_output), enable_shell=True)
        self.assertTrue(retcode == 0)
        self.assertEqual(out.strip(), self.valid_output)

    def test_program_failure(self):
        success, out, err = run_through_shell("thisshouldtriggeranerror")
        self.assertFalse(success)
