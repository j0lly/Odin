# -*- coding: utf-8 -*-
'''
testing module for the worker and dns discovery library
'''

import pytest

from odin.worker import Worker


def test_worker_ip_range():
    worker = odin.Worker('string')

