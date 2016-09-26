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
    """ this function perform a dns scan and optionally store results in DB
    and/or dump them to file

    :param target: cidr range
    :type target: str
    :param queue: queue object to use for multithreading
    :type queue: queue.Queue
    :param chunk_number: number of object per chunk to use for the scan
    :type chunl_number: int
    :param store: if set, store results in DB
    :type store: bool
    :param dump: if set, dump results to file
    :type dump: bool
    :param filename: name of the file to dump data to
    :type filename: str
    """

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
