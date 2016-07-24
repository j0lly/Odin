# -*- coding: utf-8 -*-
'''
testing module for the worker and dns discovery library
'''

import dns.resolver
from mock import patch
from odin.worker import Worker

IP = '192.168.0.1'


@patch('dns.resolver.Resolver')
class TestWoker:

    def test_resolve_no_timeout(self, m_dns):
        worker = Worker(IP)
        assert worker._resolver.timeout == 1
        assert worker.resolve() == (True, True)

    def test_resolve_timeout(self, m_dns):
        worker = Worker(IP)
        assert worker._resolver.timeout == 1
        assert worker.resolve(timeout=2) == (True, True)
        assert worker._resolver.timeout == 2

    def test_resolve_NoAnswer(self, m_dns):
        m_dns().query.side_effect = dns.resolver.NoAnswer('foo')
        worker = Worker(IP)
        assert worker.resolve() == (True, False)

    def test_resolve_NoNameservers(self, m_dns):
        m_dns().query.side_effect = dns.resolver.NoNameservers('foo')
        worker = Worker(IP)
        assert worker.resolve() == (True, False)

    def test_resolve_Timeout(self, m_dns):
        m_dns().query.side_effect = dns.resolver.Timeout('foo')
        worker = Worker(IP)
        assert worker.resolve() == (False, False)

    def test_dns_scan(self, m_dns):
        pass

    def test_dns_version(self, m_dns):
        pass
