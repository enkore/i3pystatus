#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest

from i3pystatus.core.modules import IntervalModule


class IntervalModuleMetaTest(unittest.TestCase):

    def test_no_settings(self):
        class NoSettings(IntervalModule):
            pass
        self.assertTrue('interval' in NoSettings.settings)

    def test_no_interval_setting(self):
        class NoIntervalSetting(IntervalModule):
            settings = (('option', 'desc'),)
        self.assertEqual(NoIntervalSetting.settings,
                         (('option', 'desc'), 'interval'))

    def test_settings_with_interval(self):
        class SettingsInteval(IntervalModule):
            settings = ('option', 'interval')
        self.assertEqual(SettingsInteval.settings, ('option', 'interval'))

    def test_settings_with_interval_desc(self):
        class SetttingsIntervalDesc(IntervalModule):
            settings = (('interval', 'desc'),)
        self.assertEqual(SetttingsIntervalDesc.settings,
                         (('interval', 'desc'),))
