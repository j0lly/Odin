#!/usr/bin/env python
# filename: resolver.py

''' resolver module: the actual DNS query & the Version checkeri '''

import dns.resolver
import time

class Resolve(object):
    '''
    perform a dns query against the target and retrive the answer.

    :param target: ip to run the query against
    :type target: str
    :param record: subject of the query
    :type record: str
    :param rtype: DNS record type
    :type rtype: str
    :param timeout: set a timeout for the DNS resolution
    :type timeout: int
    :returns: timestamp of the scan along with results (is dns and resolves)
    :rtype: tuple
    '''

    def __init__(self, target):

        self.resolver = dns.resolver.Resolver()
        self.resolver.nameservers = [target]
        self.resolver.timeout = 4
        self.resolver.lifetime = 4

    def resolve(self, timeout=None, record='www.yahoo.com', rtype='NS'):
        ''' perform a dns query against the target and retrive the answer. '''

        if timeout:
            self.resolver.timeout = timeout
        is_dns = False
        timestamp = int(time.time())
        try:
            self.resolver.query(record, rtype)
            is_resolver = True
            is_dns = True
        except dns.resolver.NoAnswer:
            #print('no resolver for %s'%(nameserver))
            is_resolver = False
            is_dns = True
        # timeout, NXDOMAIN and so on
        except:
            # logging exception
            pass
            # sys.exit()

        return tuple(timestamp, is_dns, is_resolver)


    def version(self):
        ''' scan target for version
        '''
        return None
