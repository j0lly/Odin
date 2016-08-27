# -*- coding: utf-8 -*-
'''
testing module for utils module
'''

import ipaddress
import pytest
from mock import patch, Mock
from odin.utils import findip, chunker, run_scan


class TestFindip:
    """ test findip obj """

    def test_findip_raise_addressvalueerror_str(self):
        with pytest.raises(ipaddress.AddressValueError):
            findip('a')

    def test_findip_raise_addressvalueerror_float(self):
        with pytest.raises(ipaddress.AddressValueError):
            findip(1.00)

    def test_findip_raise_addressvalueerror_fake_ip(self):
        with pytest.raises(ipaddress.AddressValueError):
            findip('192.11.1.500')

    def test_findip_raise_netmaskvalueerror(self):
        """ only 1-32 is allowed as a valid netmask """
        with pytest.raises(ipaddress.NetmaskValueError):
            findip('192.168.0.1/39')

    def test_single_address_netmask(self):
        assert findip('192.168.1.1/32') == ['192.168.1.1']

    def test_single_address(self):
        assert findip('192.168.1.1') == ['192.168.1.1']

    def test_ip_range(self):
        assert findip('192.168.1.1/29') == ['192.168.1.1', '192.168.1.2',
                                            '192.168.1.3', '192.168.1.4',
                                            '192.168.1.5', '192.168.1.6']


class TestChunker:
    """ ditto """

    def test_yield_iterables(self):
        assert list(chunker([1, 2, 3], 2)) == [[1, 2], [3]]


class TestRunScan:
    """ testing a function that use threads and other voodoos... """
    # FIXME 1 day create also test fr multiple targets

    def test_run_scan_filter_all(self):
        scanned_ip = {
                    "class_b": "82.81",
                    "ip": "82.81.118.81",
                    "is_dns": False,
                    "is_resolver": False,
                    "timestamp": "2016-08-27 13:09:38 -00:00",
                    "version": None,
                    }

        m_cls = Mock
        m_cls.start = Mock
        m_cls.join = Mock
        m_cls.attribute_values = scanned_ip
        m_cls.serialize = scanned_ip
        m_cls.ip = scanned_ip['ip']
        queue = Mock()
        queue.empty.side_effect = [False, True]
        queue.get.return_value = m_cls
        assert run_scan('all', queue,
                        [['192.168.0.1']],
                        cls=m_cls) == {scanned_ip['ip']: scanned_ip}

    def test_run_scan_filter_is_dns_not(self):
        scanned_ip = {
                    "class_b": "82.81",
                    "ip": "82.81.118.81",
                    "is_dns": False,
                    "is_resolver": False,
                    "timestamp": "2016-08-27 13:09:38 -00:00",
                    "version": None,
                    }

        m_cls = Mock
        m_cls.start = Mock
        m_cls.join = Mock
        m_cls.attribute_values = scanned_ip
        m_cls.serialize = scanned_ip
        m_cls.ip = scanned_ip['ip']
        m_cls.is_dns = scanned_ip['is_dns']
        queue = Mock()
        queue.empty.side_effect = [False, True]
        queue.get.return_value = m_cls
        assert run_scan('is_dns', queue,
                        [['192.168.0.1']],
                        cls=m_cls) == {}
