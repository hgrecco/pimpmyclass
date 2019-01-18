# -*- coding: utf-8 -*-

import unittest

import statistics as stats
import random

from pimpmyclass.stats import RunningStats, stats as calc_stats


class StatsTest(unittest.TestCase):

    def test_grouping(self):
        rs = RunningStats()
        for key in ('first', 'second'):
            values = [random.random() for _ in range(20)]
            for ndx, value in enumerate(values, 1):
                rs.add(key, value)
                if ndx == 1:
                    continue
                s = rs.stats(key)

                self.assertAlmostEqual(rs[key].last, value)
                self.assertAlmostEqual(rs[key].count, ndx)
                self.assertAlmostEqual(rs[key].sum, sum(values[:ndx]))
                self.assertAlmostEqual(rs[key].sum2, sum(v ** 2 for v in values[:ndx]))
                self.assertAlmostEqual(rs[key].min, min(values[:ndx]))
                self.assertAlmostEqual(rs[key].max, max(values[:ndx]))

                self.assertAlmostEqual(s.last, value)
                self.assertAlmostEqual(s.count, ndx)
                self.assertAlmostEqual(s.mean, stats.mean(values[:ndx]))
                self.assertAlmostEqual(s.std, stats.pstdev(values[:ndx]))
                self.assertAlmostEqual(s.min, min(values[:ndx]))
                self.assertAlmostEqual(s.max, max(values[:ndx]))

    def test_wrong_attribute(self):
        rs = RunningStats()
        with self.assertRaises(AttributeError):
            out = rs.non_existing_attr

    def test_failed(self):
        rs = RunningStats()
        with rs.time('test'):
            x = 0

        with self.assertRaises(Exception):
            with rs.time('test'):
                raise Exception

        self.assertEqual(rs.stats('test').count, 1)
        self.assertEqual(rs.stats('failed_test').count, 1)

    def test_empty(self):
        rs = RunningStats()
        self.assertEqual(rs.stats('test'), (0, ) * 6)
        with rs.time('test'):
            x = 0
        self.assertNotEqual(rs.stats('test'), (0, ) * 6)
        self.assertEqual(rs.stats('other'), (0, ) * 6)

    def test_empty_calc(self):
        rs = RunningStats()
        self.assertEqual(calc_stats(rs.stats('test')), (0, ) * 6)
