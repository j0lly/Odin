# -*- coding: utf-8 -*-
'''
testing module for the worker and dns discovery library
'''

from dns import resolver
from mock import patch, Mock
from odin.worker import Worker

IP = '192.168.0.1'


@patch('dns.resolver.Resolver')
class TestWoker:
    """ test worker obj"""

    def test_resolve_no_timeout(self, m_dns):
        worker = Worker(IP)
        assert worker._resolver.timeout == 1
        assert worker.resolve() == (True, True)

    def test_resolve_with_timeout(self, m_dns):
        worker = Worker(IP)
        assert worker._resolver.timeout == 1
        assert worker.resolve(timeout=2) == (True, True)
        assert worker._resolver.timeout == 2

    def test_resolve_NoAnswer(self, m_dns):
        m_dns().query.side_effect = resolver.NoAnswer('foo')
        worker = Worker(IP)
        assert worker.resolve() == (True, False)

    def test_resolve_NoNameservers(self, m_dns):
        m_dns().query.side_effect = resolver.NoNameservers('foo')
        worker = Worker(IP)
        assert worker.resolve() == (True, False)

    def test_resolve_Timeout(self, m_dns):
        m_dns().query.side_effect = resolver.Timeout('foo')
        worker = Worker(IP)
        assert worker.resolve() == (False, False)

    def test_dns_version_no_timeout(self, m_dns):
        answers = []
        record = Mock
        record.strings = ['some'.encode(), 'other stuff'.encode()]
        answers.append(record)
        m_dns().query.return_value = answers
        worker = Worker(IP)
        assert worker._resolver.timeout == 1
        assert worker.dns_version() == answers[0].strings[0].decode()

    def test_dns_version_with_timeout(self, m_dns):
        answers = []
        record = Mock
        record.strings = ['some'.encode(), 'other stuff'.encode()]
        answers.append(record)
        m_dns().query.return_value = answers
        worker = Worker(IP)
        assert worker._resolver.timeout == 1
        assert worker.dns_version(timeout=2) == answers[0].strings[0].decode()
        assert worker._resolver.timeout == 2

    def test_dns_version_NoNameservers(self, m_dns):
        m_dns().query.side_effect = resolver.NoNameservers('foo')
        worker = Worker(IP)
        assert worker.dns_version() is None

    def test_dns_version_Timeout(self, m_dns):
        m_dns().query.side_effect = resolver.Timeout('foo')
        worker = Worker(IP)
        assert worker.dns_version() is None

    def test_dns_scan(self, m_dns):
        answers = []
        record = Mock
        record.strings = ['some version'.encode(), 'other stuff'.encode()]
        answers.append(record)
        m_dns().query.side_effect = [True, answers]
        worker = Worker(IP)
        assert worker.dns_scan() is True
        assert worker.is_dns is True
        assert worker.is_resolver is True
        assert worker.version == 'some version'

    def test_dns_scan_without_version(self, m_dns):
        m_dns().query.return_value = 'whatever'
        worker = Worker(IP)
        assert worker.dns_scan(version=False) is True
        assert worker.is_dns is True
        assert worker.is_resolver is True
        assert worker.version is None
