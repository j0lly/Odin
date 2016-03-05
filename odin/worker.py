# -*- coding: utf-8 -*-

'''
this module provide the worker object; an asyncronous dns data miner
'''

import time
import dns.resolver
from .exceptions import TooManyIPsException

class Worker(object):
    ''' create a Worker onbejct, able to open a socket and run a batch '''

    def __init__(self, ip_range, worker='async'):
        self.ip_list = ip_range
        self.worker = worker

    def __endpoint__(self):
        return None

    def retrive(self):
        return None

    def batch(self):
        return None

    def scan(self):
        ''' make a simple scan for test porpouses; No more than 128 IPs will be
            scanned. It returns a dictionary wit ip and status (dns or open resolver)
        :param ip_list: list of IPs to be scanned for open Resolvers
        :type ip_list: list
        :returns: a dictionary with the result of the scan
        :rtype: dict
        '''
        if len(self.ip_list) > 128:
            raise TooManyIPsException('scan() is suppoused to run over a \
                    maximum of 128 IPs. Use batch() for bigger chunks')
        result = list()
        for ip_target in self.ip_list:
            timestamp = dict(timestamp=int(time.time()))
            target = Resolve(ip_target)
            try:
                info = target.resolve()
            except:
                #need to be catched
                raise
            if info['is_dns'] is True:
                try:
                    version = target.version()
                except:
                    raise
            else:
                version = dict(version=False)
            result.append({ip_target: {**info, **version, **timestamp}})
        return result


class Resolve(object):
    '''
    create a query object with a target as the nameserver.

    :param target: ip to run the query against
    :type target: str
    '''

    def __init__(self, target):

        self.resolver = dns.resolver.Resolver()
        self.resolver.nameservers = [target]
        self.resolver.timeout = 2
        self.resolver.lifetime = 2

    def resolve(self, timeout=None, record='www.yahoo.com', rtype='CNAME'):
        ''' perform a dns query against the target and retrive the answer.
        :param timeout: set a timeout for the DNS resolution
        :type timeout: int
        :param record: subject of the query
        :type record: str
        :param rtype: DNS record type
        :type rtype: str
        :returns: return if target is dns and is an openresolver
        :rtype: dict
        '''

        if timeout:
            self.resolver.timeout = timeout
        is_dns = False
        is_resolver = False
        try:
            self.resolver.query(record, rtype)
            is_dns = True
            is_resolver = True
        except dns.resolver.NoAnswer:
            #print('no resolver for %s'%(nameserver))
            is_dns = True
        except dns.exception.Timeout:
            # assumes no DNS behind IP
            pass
        #NXDOMAIN and so on
        except:
            raise
        return dict(is_dns=is_dns, is_resolver=is_resolver)


    def version(self, timeout=None):
        ''' scan target for version
        :param timeout: set a timeout for the DNS resolution
        :type timeout: int
        :returns: return version and type
        :rtype: dict
        '''
        if timeout:
            self.resolver.timeout = timeout
        try:
            answer = self.resolver.query('version.bind', 'TXT', 'CHAOS')
        except dns.resolver.NoNameservers:
            raise
        except dns.exception.Timeout:
            return dict(version=False)
        return dict(version=answer[0].strings[0]) #return version string for NS
