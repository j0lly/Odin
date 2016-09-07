# -*- coding: utf-8 -*-

"""collection of helpers for Miner module."""

import ipaddress
import json
import odin
from odin.store import ThreadedModel, OpenDnsModel

# Default logging capabilities (logging nowhere)
log = odin.get_logger()


def findip(string):
    """calculate hosts to be scanned; it's just an helper.

    :param string: ip range in cidr notation
    :type string: str
    :returns: a list of IPs to be scanned
    :rtype: list
    """
    try:
        ip_range = ipaddress.IPv4Network(string, strict=False)
    except ipaddress.AddressValueError as err:
        log.error('%s', err, exc_info=True)
        raise
    except ipaddress.NetmaskValueError as err:
        log.error('%s', err, exc_info=True)
        raise
    if ip_range.num_addresses == 1:
        log.debug('value resulted in a single host ip: %s',
                  ip_range.network_address.compressed)
        return [ip_range.network_address.compressed]
    else:
        log.debug('value resulted in a muliple host list for %s',
                  string)
        return [k.compressed for k in ip_range.hosts()]


def chunker(iterable, chunk_size=16):
    """return a list of iterables chunking the initial iterable.

    :param iterable: an iterable to cut in chunks
    :type iterable: iter
    :param chunk_size: chunk lenght to use
    :type chunk_size: int
    :returns: a generator of lists of chunks of provided iterable
    :rtype: generator
    """
    for x in range(0, len(iterable), chunk_size):
        log.debug('yielding %s', iterable[x:x+chunk_size])
        yield iterable[x:x+chunk_size]


def run_scan(queue, targets, cls=ThreadedModel):
    """ Run a scan against targets and return a Pynamo modeled list of objects.

    :queue: a queue
    :type queue: queue.Queue
    :param targets: list of ips, divided in chunks if necessary
    :type targets: list
    :param cls: class to be used for resolution and threading
    :type cls: class object
    :returns: yield a list of pynamo objects
    :rtype: generator
    """

    for chunk in targets:
        threads = []
        for ip in chunk:
            obj = cls(object=OpenDnsModel(ip), queue=queue)
            obj.daemon = True
            threads.append(obj)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=2)

        while not queue.empty():
            ip_info = queue.get()
            yield ip_info


def generate_serialized_results(query, output='json'):
    """Simple helper to generate usable output from a pynamo query
    :param query: a pynamo query that returned a generator
    :type query: generator
    :param output: format of the utput, for now just json or byte format
    :type output: str
    :returns: a dictionary generator of serialized pynamodb objects
    :rtype: generator
    """
    for result in query:
        obj = result.serialize
        if output == 'json':
            yield '{}\n'.format(json.dumps(obj, indent=4))
        elif output == 'bytes':
            yield '{}\n'.format(json.dumps(obj, indent=4)).encode('utf-8')
        elif output is None:
            yield obj


def assembler(string):
    """get a str with class a, b or c range in the form:
       192, 192.168, 192.168.0 and return proper CIDR address like 192.0.0.0/8
    """
    class_range = ['class_c', 'class_b', 'class_a']
    missing = 4 - len(string.split('.'))
    log.debug('building cidr with %s missing dots', missing)
    for dots in range(0, missing):
        string += '.0'
    return (string+'/'+str(int(24/missing)), class_range[missing-1])


def get_filter(string):
    """build filter string and assert if negation is in place"""
    if string[0] is '!':
        return(string[1:], True)
    else:
        return(string, False)
