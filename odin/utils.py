# -*- coding: utf-8 -*-

"""collection of helpers for Miner module."""

import ipaddress


def findip(string):
    """calculate hosts to be scanned; it's just an helper.

    :param string: ip range in cidr notation
    :type string: str
    :returns: a generator of IPs to be scanned
    :rtype: generator
    """
    try:
        ip_range = ipaddress.IPv4Network(string, strict=False)
    except ipaddress.AddressValueError:
        raise
    except ipaddress.NetmaskValueError:
        raise
    if ip_range.num_addresses == 1:
        return ip_range.network_address.compressed
    else:
        for k in ip_range.hosts():
            return k.compressed


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
