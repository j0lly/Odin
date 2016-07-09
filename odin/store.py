# -*- coding: utf-8 -*-
'''
abstraction layer for storing miner results
'''
from .worker import Worker
from pynamodb.models import Model
from pynamodb.indexes import GlobalSecondaryIndex, AllProjection
from pynamodb.attributes import UTCDateTimeAttribute, UnicodeAttribute, BooleanAttribute

class NetMasks(GlobalSecondaryIndex):
    """
    This class represents a global secondary index
    """
    class Meta:
        # index_name is optional, but can be provided to override the default name
        index_name = 'NetMaskOD'
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
        table_name = 'OpenDns'
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
