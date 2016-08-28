# -*- coding: utf-8 -*-

"""odin [Open Dns INspector].

A micro WebService that implement standard methods to batch
scan the network and find Open DNS resolvers, storing results in convenient way

:copyright: (c) 2016 by J0lly.
:license: BSD, see LICENSE for more details.
"""

import logging


def get_logger(log_value=None):
    """ prepare the logger and return one configured """
    logger = logging.getLogger(__name__)
    if log_value is None:
        handler = logging.NullHandler()
    else:
        handler = logging.StreamHandler()
        logger.setLevel(log_value)
    formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
