# -*- coding: utf-8 -*-

"""
core utils for Cli and Webapp
"""

import odin
from odin import utils
from odin.tasks import odin_store, odin_dump

# Default logging capabilities (logging nowhere)
log = odin.get_logger()


def do_scan(target, queue,
            chunk_number=25, store=True,
            dump=False, filename=None):

    targets = utils.findip(target)
    log.debug('list of ip to be scanned: %s', targets)
    targets = utils.chunker(targets, chunk_number)

    for chunk in targets:

        result = []

        for obj in utils.run_scan(queue, chunk):
            log.debug('adding %s to the resultset', obj.ip)
            result.append(obj)

        if store:
            log.info('store flag passed: saving results into the DB..')
            odin_store.delay(result)

        if dump:
            log.info('dump flag passed: saving results to file..')
            odin_dump.delay(result, filename=filename)

        for i in result:
            yield i
