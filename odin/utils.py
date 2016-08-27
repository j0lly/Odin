# -*- coding: utf-8 -*-

"""collection of helpers for Miner module."""

import ipaddress
from odin.store import ThreadedModel


def findip(string):
    """calculate hosts to be scanned; it's just an helper.

    :param string: ip range in cidr notation
    :type string: str
    :returns: a list of IPs to be scanned
    :rtype: list
    """
    try:
        ip_range = ipaddress.IPv4Network(string, strict=False)
    except ipaddress.AddressValueError:
        raise
    except ipaddress.NetmaskValueError:
        raise
    if ip_range.num_addresses == 1:
        return [ip_range.network_address.compressed]
    else:
        return [k.compressed for k in ip_range.hosts()]


def chunker(iterable, chunk_size):
    """return a list of iterables chunking the initial iterable.

    :param iterable: an iterable to cut in chunks
    :type iterable: iter
    :param chunk_size: chunk lenght to use
    :type chunk_size: int
    :returns: a generator of lists of chunks of provided iterable
    :rtype: generator
    """
    for x in range(0, len(iterable), chunk_size):
        yield iterable[x:x+chunk_size]


def run_scan(filter, queue, targets, cls=ThreadedModel):
    """ Run a scan against targets and return a Pynamo modeled list of objects.
    :param filter: chose how any attributes to store in the reply
    :type args: str
    :queue: a queue
    :type queue: queue.Queue
    :param targets: list of ips, divided in chunks if necessary
    :type targets: list
    :param cls: class to be used for resolution and threading
    :type cls: class object
    :returns: a dict of pynamo objects, and the ip as the key
    :rtype: dict
    """

    result = {}

    for chunk in targets:
        threads = []
        for ip in chunk:
            obj = cls(ip, queue=queue)
            obj.daemon = True
            threads.append(obj)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=2)

        while not queue.empty():
            ip_info = queue.get()
            if filter == 'all':
                result.update({ip_info.ip: ip_info.serialize})
            elif getattr(ip_info, filter):
                result.update({ip_info.ip: ip_info.serialize})

    return result
