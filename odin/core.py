#!/usr/bin/env python
# filename: core.py

''' collection of helpers for Miner module '''

import ipaddress

def findip(string):
    ''' calculate hosts to be scanned; it's just an helper
    :param string: ip range in cidr notation
    :type string: str
    :returns: list of IPs to be scanned
    :rtype: list
    '''
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
