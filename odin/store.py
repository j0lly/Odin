# -*- coding: utf-8 -*-
'''
abstraction layer for storing miner results
'''

import botocore
from boto3.session import Session
from .static import TABLE
from .exceptions import StoreBadParameter

class Store(object):
    '''
    The main interface object; it takes session information and data layer type.
    session can be credentials, a file or whatever will be evaluated as the
    method to connect to the datastore
    '''

    def __init__(self, session, table=TABLE, store='dynamodb', session_args=None):
        ''' Istantiate connection to Data Store and Table '''
        # Need lots of sanity checks
        self.session = session
        self._session_args = session_args
        self._store = store
        self._table = table

    def __endpoint__(self):
        ''' get info about store schema '''
        schema = dict()
        get = self.session(**self._session_args)
        if self._store is 'dynamodb':
            tables = get.meta.client.list_tables()['TableNames']
            for table in tables:
                tab = get.Table(table)
                tab_schema = tab.key_schema
                tab_secondary_index = tab.local_secondary_indexes
                tab_global_sec_index = tab.global_secondary_indexes
                schema[table] = dict(schema=tab_schema,
                                     local_index=tab_secondary_index,
                                     global_index=tab_global_sec_index)

        return {self._store : schema}

    def _create_table(self, **kwargs):
        '''	wrapper for creating Tables and/or Items
        :param :
        '''
        pass
#		# Create the DynamoDB table.
#		table = dynamodb.create_table(
#			TableName='users',
#			KeySchema=[
#				{
#					'AttributeName': 'username',
#					'KeyType': 'HASH'
#				},
#				{
#					'AttributeName': 'last_name',
#					'KeyType': 'RANGE'
#				}
#			],
#			AttributeDefinitions=[
#				{
#					'AttributeName': 'username',
#					'AttributeType': 'S'
#				},
#				{
#					'AttributeName': 'last_name',
#					'AttributeType': 'S'
#				},
#
#			],
#			ProvisionedThroughput={
#				'ReadCapacityUnits': 5,
#				'WriteCapacityUnits': 5
#			}
#		)
#
#		# Wait until the table exists.
#		table.meta.client.get_waiter('table_exists').wait(TableName='users')

    def query(self):
        ''' make a query to the Data Store
        '''
        pass

    def get(self, items=None):
        '''
        get one or multiple Items from the Data Store.
        Items need to be passed as list of keys.
        [
         {'network': 13,
          'ip': '13.1.1.1'},
         {'network': 13,
          'ip': '13.1.1.2'},
         {'network': 55,
          'ip': '14.3.4.5'}
        ]
        :param items: a list of object to be retrived, or empty for the item count
        :type items: list
        :return: a dictionary with possible results
        :rtype: dict
        '''
        get = self.session(**self._session_args).Table(self._table)
        # get Table cunt if table passedd
        if not items:
            return  dict(ItemsCount=get.item_count)
        # get a serialized getItem on all the data series
        try:
            result = get.batch_get_item(
                RequestItems={
                    self._table: {'Keys': items}
                    })
        except botocore.exceptions.ClientError:
            raise StoreBadParameter(
                'items provided does not follow the correct Table schema')
        #TODO: add found vs queried in response
        return result

    def push(self, items=None):
        ''' create one or multiple Items like:
            [
             {'network': 17,
              'ip': '17.5.1.1',
              'timestamp': 11111111,
              'is_dns': True,
              'is_resolver': True
             },
             {'network': 17,
              'ip': '13.3.44.42',
              'timestamp': 11111111,
              'is_dns': True,
              'is_resolver': True
             },
             {'network': 55,
              'ip': '55.14.123.6',
              'timestamp': 11111111,
              'is_dns': True,
              'is_resolver': True
             }
            ]
        :param items: list of item to be inserted in the table
        :type items: list

        '''
        session = self.session(**self._session_args).Table(self._table)
        try:
            with session.batch_writer() as batch:
                for item in items:
                    batch.put_item(Item=item)
        except botocore.exceptions.ClientError:
            raise StoreBadParameter(
                'items provided does not follow the correct Table schema')

    def update(self):
        ''' update a single Item
        '''
        pass

#TODO: let it become an internal @staticmethod
def get_resource(key=None, secret=None, region=None, endpoint_url=None):
    ''' get boto3 session fr dynamo
    :param key: isfpassed, a aws key
    :type key: str
    :param secret: if passed, a aws secret
    :type secret: str
    :param region: if passed, a region name
    :type region: str
    :returns: a boto3 sesion object
    :rtype: boto3.Session.session
    '''
    # take default from .aws/* files
    session = Session(aws_access_key_id=key,
                      aws_secret_access_key=secret,
                      region_name=region)

    return session.resource('dynamodb', endpoint_url=endpoint_url)
