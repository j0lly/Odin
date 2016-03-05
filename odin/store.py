# -*- coding: utf-8 -*-
'''
abstraction layer for storing miner results
'''

import exceptions

class Store(object):
    '''
    The main interface object; it takes session information and data layer type.
    session can be credentials, a file or whatever will be evaluated as the
    method to connect to the datastore
    '''

    def __init__(self, session):
        # Need lots of sanity checks
        self.session = session
    def __endpoint__(self):
        pass
    def query(self):
        pass
    def get(self):
        pass
    def put(self):
        pass
    def update(self):
        pass
    def create(self):
        pass

