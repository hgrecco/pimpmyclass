# -*- coding: utf-8 -*-
"""
    lantz_core.stats
    ~~~~~~~~~~~

    Implements an statistical accumulator

    :copyright: 2018 by Lantz Authors, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""

from collections import namedtuple
from contextlib import contextmanager
from time import perf_counter

#: Data structure
Stats = namedtuple('Stats', 'last count mean std min max')


def stats(state):
    """Return the statistics for given state.

    Parameters
    ----------
    state : RunningState

    Returns
    -------
    Stats named tuple
    """
    if not state.count:
        return Stats(0, 0, 0, 0, 0, 0)

    mean = state.sum / state.count
    std = (float(state.sum2 - 2.0 * state.sum * mean + state.count * mean ** 2.0) / float(state.count)) ** 0.5
    return Stats(state.last, state.count,
                 mean, std, state.min, state.max)


class RunningState:
    """Accumulator for events.

    Parameters
    ----------
    value :
        first value to add.

    Returns
    -------

    """

    def __init__(self, value=None):
        if value is not None:
            self.add(value)

    def __getattr__(self, key):
        if key in ('last', 'count', 'sum', 'sum2'):
            return 0
        if key == 'min':
            return float('inf')
        if key == 'max':
            return float('-inf')
        raise AttributeError('{} is not a valid attribute of RunningState'.format(key))

    def add(self, value):
        """Add to the accumulator.

        Parameters
        ----------
        value :
            value to be added.

        Returns
        -------

        """
        self.last = value
        self.count += 1
        self.sum += value
        self.sum2 += value * value
        self.min = min(self.min, value)
        self.max = max(self.max, value)


class RunningStats(dict):
    """Accumulator for categorized event statistics.
    """

    def add(self, key, value):
        """Add an event to a given accumulator.

        Parameters
        ----------
        key :
            category to which the event should be added.
        value :
            value of the event.

        Returns
        -------

        """
        if key in self:
            super().__getitem__(key).add(value)
        else:
            super().__setitem__(key, RunningState(value))

    def stats(self, key):
        """Return the statistics for the current accumulator.

        Parameters
        ----------
        key :
            

        Returns
        -------

        """
        if key in self:
            return stats(super().__getitem__(key))
        else:
            return Stats(0, 0, 0, 0, 0, 0)

    @contextmanager
    def time(self, key):
        tic = perf_counter()
        try:
            yield
            self.add(key, perf_counter() - tic)
        except Exception as e:
            self.add('failed_' + key, perf_counter() - tic)
            raise e