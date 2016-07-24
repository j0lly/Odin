# -*- coding: utf-8 -*-

'''
abstraction layer for storing miner results
'''

import threading
from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.attributes import (UTCDateTimeAttribute, UnicodeAttribute,
                                 BooleanAttribute)
from .worker import Worker
from .static import TABLE, G_SEC_INDEX


class NetMasks(GlobalSecondaryIndex):
    """
    This class represents a global secondary index
    """
    class Meta:
        index_name = G_SEC_INDEX
        read_capacity_units = 5
        write_capacity_units = 5
        # All attributes are projected
        projection = AllProjection()

    # This attribute is the hash key for the index
    # Note that this attribute must also exist
    # in the model
    netmask = UnicodeAttribute(default=None, hash_key=True)
    timestamp = UTCDateTimeAttribute(range_key=True)


class OpenDnsModel(Worker, Model):
    ''' Model for Dns inserts '''
    class Meta:
        table_name = TABLE
        host = 'http://127.0.0.1:8000'

    ip = UnicodeAttribute(hash_key=True)
    netmask = UnicodeAttribute(default=None)
    timestamp = UTCDateTimeAttribute(range_key=True)
    is_dns = BooleanAttribute(default=False)
    is_resolver = BooleanAttribute(default=False)
    version = UnicodeAttribute(default=None)
    netmasks = NetMasks()

    def __init__(self, *args, **kwargs):
        super(OpenDnsModel, self).__init__(*args, **kwargs)
        self.netmask = '.'.join(self.ip.split('.')[0:2])


class ThreadedModel(OpenDnsModel, threading.Thread):
    class Meta:
        table_name = TABLE
        host = 'http://127.0.0.1:8000'

    ip = UnicodeAttribute(hash_key=True)
    netmask = UnicodeAttribute(default=None)
    timestamp = UTCDateTimeAttribute(range_key=True)
    is_dns = BooleanAttribute(default=False)
    is_resolver = BooleanAttribute(default=False)
    version = UnicodeAttribute(default=None)
    netmasks = NetMasks()

    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self)
        self.queue = kwargs.pop('queue')
        super(ThreadedModel, self).__init__(*args, **kwargs)

    def run(self, version=True, block=True, timeout=2):
        self.dns_scan(version)
        self.queue.put(self.attribute_values, block, timeout)
        self.queue.task_done()
