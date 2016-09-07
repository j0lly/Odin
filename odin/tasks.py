# -*- coding: utf-8 -*-

"""
Async classes
"""

from celery import Celery
import odin
from odin.store import OpenDnsModel

# Default logging capabilities (logging nowhere)
log = odin.get_logger()


async = Celery('tasks',
               backend='redis://localhost:6379',
               broker='redis://localhost:6379')


@async.task
def odin_store(resultset):
    try:
        with OpenDnsModel.batch_write() as batch:
            for ip in resultset:
                log.debug('storing ip: %s', ip)
                batch.save(ip)
    except Exception as err:
        log.error('batch failed to save to db: %s', err, exc_info=True)
        pass

    return True
