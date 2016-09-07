# -*- coding: utf-8 -*-

"""
Async classes
"""

import uuid
import json
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


@async.task
def odin_dump(resultset, filename=str(uuid.uuid4())):
    with open(filename, 'wa') as f:
        json.dump([r.serialize for r in resultset if r.serialize['is_dns']], f)
