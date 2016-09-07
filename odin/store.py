# -*- coding: utf-8 -*-

"""
abstraction layer for storing miner results
"""

import threading
import queue
import arrow
from pynamodb.models import Model
from pynamodb.indexes import (GlobalSecondaryIndex, AllProjection)
from pynamodb.attributes import (UTCDateTimeAttribute, UnicodeAttribute,
                                 BooleanAttribute)
import odin
from odin.worker import Worker
from odin.static import (TABLE, RESOLVERS_GLOBAL_INDEX, CLASS_B_GLOBAL_INDEX,
                         DNS_GLOBAL_INDEX, DNS_RC, DNS_WC,
                         CLASSB_RC, CLASSB_WC, RESOLVERS_RC, RESOLVERS_WC,
                         CLASS_A_GLOBAL_INDEX, CLASSA_RC, CLASSA_WC,
                         CLASS_C_GLOBAL_INDEX, CLASSC_RC, CLASSC_WC)

# Default logging capabilities (logging nowhere)
log = odin.get_logger()


class ClassA(GlobalSecondaryIndex):
    """
    This class represents a global secondary index
    """
    class Meta:
        index_name = CLASS_A_GLOBAL_INDEX
        read_capacity_units = CLASSA_RC
        write_capacity_units = CLASSA_WC
        # All attributes are projected
        projection = AllProjection()

    class_a = UnicodeAttribute(hash_key=True)
    timestamp = UTCDateTimeAttribute(range_key=True)


class ClassB(GlobalSecondaryIndex):
    """
    This class represents a global secondary index
    """
    class Meta:
        index_name = CLASS_B_GLOBAL_INDEX
        read_capacity_units = CLASSB_RC
        write_capacity_units = CLASSB_WC
        # All attributes are projected
        projection = AllProjection()

    class_b = UnicodeAttribute(hash_key=True)
    timestamp = UTCDateTimeAttribute(range_key=True)


class ClassC(GlobalSecondaryIndex):
    """
    This class represents a global secondary index
    """
    class Meta:
        index_name = CLASS_C_GLOBAL_INDEX
        read_capacity_units = CLASSC_RC
        write_capacity_units = CLASSC_WC
        # All attributes are projected
        projection = AllProjection()

    class_c = UnicodeAttribute(hash_key=True)
    timestamp = UTCDateTimeAttribute(range_key=True)


class ResolversIndex(GlobalSecondaryIndex):
    """
    This class represents a local secondary index
    to search history of a single ip
    """
    class Meta:
        index_name = RESOLVERS_GLOBAL_INDEX
        read_capacity_units = RESOLVERS_RC
        write_capacity_units = RESOLVERS_WC
        # All attributes are projected
        projection = AllProjection()

    is_resolver = BooleanAttribute(hash_key=True)
    timestamp = UTCDateTimeAttribute(range_key=True)


class DnsIndex(GlobalSecondaryIndex):
    """
    This class represents a local secondary index
    to search history of a single ip
    """
    class Meta:
        index_name = DNS_GLOBAL_INDEX
        read_capacity_units = DNS_RC
        write_capacity_units = DNS_WC
        # All attributes are projected
        projection = AllProjection()

    is_dns = BooleanAttribute(hash_key=True)
    timestamp = UTCDateTimeAttribute(range_key=True)


class OpenDnsModel(Worker, Model):
    """ Model for dns objects """
    class Meta:
        table_name = TABLE
        host = 'http://127.0.0.1:8000'

    ip = UnicodeAttribute(hash_key=True)
    timestamp = UTCDateTimeAttribute()
    class_a = UnicodeAttribute()
    class_b = UnicodeAttribute()
    class_c = UnicodeAttribute()
    is_dns = BooleanAttribute(default=False)
    is_resolver = BooleanAttribute(default=False)
    version = UnicodeAttribute(null=True, default=None)
    class_a_index = ClassA()
    class_b_index = ClassB()
    class_c_index = ClassC()
    openresolvers_index = ResolversIndex()
    dns_index = DnsIndex()

    def __init__(self, *args, **kwargs):
        super(OpenDnsModel, self).__init__(*args, **kwargs)
        self.class_a = '.'.join(self.ip.split('.')[0:1])
        self.class_b = '.'.join(self.ip.split('.')[0:2])
        self.class_c = '.'.join(self.ip.split('.')[0:3])

    @property
    def serialize(self):
        """ take important values and prepare them form printing """
        result = dict(
            ip=self.ip,
            class_a=self.class_a,
            class_b=self.class_b,
            class_c=self.class_c,
            is_dns=self.is_dns,
            is_resolver=self.is_resolver,
            version=self.version,
            timestamp=arrow.get(
                self.timestamp).format(
                    'YYYY-MM-DD HH:mm:ss ZZ'))
        log.debug('serialize property called sucessfully')
        return result


class ThreadedModel(threading.Thread):
    """ Model for dns objects """

    def __init__(self, **kwargs):
        threading.Thread.__init__(self)
        self.queue = kwargs['queue']
        self.object = kwargs['object']
        self.version = kwargs.get('version', True)
        self.block = kwargs.get('block', True)
        self.timeout = kwargs.get('timeout', 2)

    def run(self):
        """ override run method
        """

        log.info('performing a dns scan operation')
        self.object.dns_scan(self.version)
        try:
            self.queue.put(self.object, self.block, self.timeout)
            log.debug('scanned object put into the queue')
        except queue.Full as err:
            log.debug('unable to put new scan result in queue, ignoring %s',
                      err,
                      exc_info=True)
        self.queue.task_done()
