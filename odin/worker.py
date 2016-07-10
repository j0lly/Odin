# -*- coding: utf-8 -*-

'''
this module provide the worker object; an asyncronous dns data miner
'''

import datetime
import dns.resolver


class Worker(object):
    ''' create a Worker object, able to open a socket and run a batch '''

    is_resolver = False
    is_dns = False
    version = None
    timestamp = datetime.datetime.now()

    def __init__(self, ip, *args, timeout=1, lifetime=1, **kwargs):
        super(Worker, self).__init__(ip, *args, **kwargs)
        self.ip = ip
        self._resolver = dns.resolver.Resolver()
        self._resolver.nameservers = [ip]
        self._resolver.timeout = timeout
        self._resolver.lifetime = lifetime


    def dns_scan(self, version=True):
        ''' make a simple scan for test porpouses; No more than 128 IPs will be
            scanned. It returns a dictionary wit ip and status (dns or open resolver)
        :param ip_list: list of IPs to be scanned for open Resolvers
        :type ip_list: list
        :returns: a dictionary with the result of the scan
        :rtype: dict
        '''
        self.is_dns, self.is_resolver = self.resolve()
        self.timestamp = datetime.datetime.now()
        if version and self.is_dns:
            self.version = self.dns_version()

        return self.__dict__

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
            self._resolver.timeout = timeout
        try:
            self._resolver.query(record, rtype)
            return (True, True)
        except (dns.resolver.NoAnswer, dns.resolver.NoNameservers):
            return (True, False)
        except dns.exception.Timeout:
            # assumes no DNS behind IP
            return (False, False)


    def dns_version(self, timeout=None):
        ''' scan target for version
        :param timeout: set a timeout for the DNS resolution
        :type timeout: int
        :returns: return version and type
        :rtype: dict
        '''
        if timeout:
            self._resolver.timeout = timeout
        try:
            answer = self._resolver.query('version.bind', 'TXT', 'CHAOS')
        except dns.resolver.NoNameservers:
            return None
        except dns.exception.Timeout:
            return None
        return answer[0].strings[0] #return version string for NS


