# -*- coding: utf-8 -*-
"""
    odin [Open Dns INspector]
    ~~~~~~~~~~~~~~~~~~~~~~~~~
    A micro WebService that implement standard methods to batch
    scan the network and find Open DNS resolvers and store results in convenient way
    :copyright: (c) 2016 by J0lly.
    :license: BSD, see LICENSE for more details.
"""

from .utils import findip
from .webapp import app
