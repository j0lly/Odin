# Design Doc

2016-02-27 V 0.1
2016-03-05 V 0.2

## Overview

Odin [Open Dns INspector] is a library that implement standard methods to batch
quaring the Web and retrive information about Open DNS resolvers and store
those information in a persistent layer. Odin also provides a facade to
interact with the stored data and retrive various informations.

## Architecture

[pic]

### functional specifications

1. a module that mine the Web and gether data relatives to Open DNS resolvers
2. a module/facade able to serialize put/get requests to the datastore
3. an api to perform data mining/retrival

#### miner

The miner is able to scan the Web taking batches of ip ranges and spot Open
DNS resolver along with some other information.

###### requirements:

* Is able to take chunks of IPs and batch over them
* Returns, for every single ip found: IP, Geographical location and (when
    possible) type and version of the DNS server and ISP/company that hold the
    server's IP.
* provide a way to return timing prediction for the current batch

#### facade

The facade provides a consistent interface to the datastore. It grants read and
write capabilities to the consumer in a standard way.

###### requirements:

* provide store agnostic calls to the datastore
* able to retrive data over the dataset of DNS information

#### api

The api is a convinient way to test the libraries and provide samples over data
mining/storing/quering. ***It implement also the possibility to query a miner
batch and retrive the actual state for the scan and the duration estimates.***

###### requirements:

* provides an API interface to use and test both miner and facade.
* query and exisiting miner job for scan time duration and estimation.
* ability to produce small scan samples
* store data in any of the supported data store

## Design

### miner design

miner is the module in charge for scanning the Web and return, for each IP, if
it is has a DNS service, if it is a Open Resolver, the timestamp of the
discovery and, if is possible, the type and version of the DNS service.

Miner expose a Miner object can be used to scan the Web in two different ways.
A serial scan can be launched; it is a blocking operation that will return a
dictionaly with the result of the scan; this method  should be used for sample
porpouses or small batches.
Another method to use Miner is to instanciate an async worker and
give it a batch to process. Miner will provide a socket from which streamed
result can be retrived. Miner provides also a retrive function that interact
with a miner worker and retrive data about the scan and the ongoing process.

#### Examples:

    worker1 = Miner.Worker(wtype='async')
    worker1.batch('10.0.0.0/16')
    ret = worker1.retrive(duration=1, scanned_hosts=1)
    
    print(ret)
    { 'duration': 71, 'scanned_hosts': 1376 }

    w_socket = worker1.__endpoint__
    checker = Miner.worker(socket=w_socket)
    ret = checker.retrive( scanned_hosts=1, time_left=1, finished=1)
    
    print(ret)
    {'scanned_hosts': 4901, 'time_left': 935, 'finished': False }

    flush = checker.flush(2)
    
    print(flush)
    {'10.0.0.1': {'timestamp': 1456603659,
                    'has_dns': True,
                    'is_openresolver': True,
                    'type': 'bind',
                    'version': False },
     '10.0.3.47': {'timestamp': 1456604210,
                    'has_dns': True,
                    'is_openresolver': False,
                    'type': False,
                    'version': False }
    }


----------------------------------------------------------

    scan = Miner.scan('10.0.0.0/24')
    
    print(scan)
    {'10.0.0.1': {'timestamp': 1456603659,
                    'has_dns': 1,
                    'is_openresolver': 1,
                    'type': 'bind',
                    'version': False
                    },
    ...
    ...
    }

If instantiated as a serial scanner, Miner provides a dictionary with all the
IPs with relatives datas.
If a worker is created, the operation is not blockng and the process will fork
in backgound providing a socket from which the scan can be controlled.
The worker will keep the results in memory untill flushed; if results are
flushed and the scan has ended, the worker object terminate himself; if data is
not retrived  after a timeout (started at scan end), the process and the
results are automatically cleaned by the worker.

### facade design

facade is the module that provide a seamless communication between a Odin data
store and a process that uses it. It provides standard call methods in order
to:

1. query the data store and retrive data in various forms (examples later)
2. create a datastore with a structure much like key:value store; the data
3. Delete a datastore
4. Make a backup of a datastore and store in a tarball
   historically cataloged in order to provide a easy to use time series data.
3. present methods to push or update data to the datastore, for single batch insertion
   with an  object or passing a stream (like a Miner object); if a stream is
   passed or the insertion is requested asyncronously the facade will provide
   a socket from insertion process control and check

#### Examples:

###### pushing

    data = dict( timestamp = 1456603659, has_dns = True, is_openresolver = True,
                type = 'bind', version = False )
    test_data = {key: value for (key, value) in [
                                                ('10.0.0.1',data),
                                                ('10.0.0.100', data),
                                                ('10.0.1.1', data)]
                                                }
    test_db = './test1'
    
    ret = Store.create(db='simple', path=test_db)
    
    print(ret)
    { 'success': True }

    storer = Store.session(test_db)
    
    socket = storer.put(test_data, method='async')
    print(storer.check(socket))
    { 'finished': True, 'errors': False, 'insertions': 3, 'pid': 23549,
    'timeout': 1823 }
    
    print(storer.delete())
    { 'success': True, 'deleted': 3 }

    print(storer.terminate(socket))
    { 'success': True }

--------------------------------------------

    data = dict( timestamp = 1456603659, has_dns = True, is_openresolver = True,
                type = 'bind', version = False )
    test_data = {key: value for (key, value) in [
                                                ('10.0.0.1',data),
                                                ('10.0.0.100', data),
                                                ('10.0.1.1', data)]
                                                }
    new_data = {'10.0.0.1': {'timestamp': 1456609411,
                    'has_dns': True,
                    'is_openresolver': True,
                    'type': 'bind',
                    'version': '9.10.3-P2' },
    test_db = './test1'
    odin_updater = = Store.session(test_db)
    ret = odin_updater.update(ip='10.0.0.1',
                            timestamp=1456603659,
                            new_data['10.0.0.1'])
    
    print(ret)
    { 'success': True,
      'warnings': 'timestamp cannot be updated',
      'value': { 1456603659 : { 'ip': '10.0.0.1', 'timestamp': 1456603659,
                                'has_dns': True, 'is_openresolver': True,
                                'type': 'bind', 'version': '9.10.3-P2' }
                                                                    }}

###### quering

    odin_query = Store.session(pth='/tmp/test1')
    get = odin_query.get('10.0.0.1') #default to the newest record
    
    print(get)
    { 1456603659 : { 'ip': '10.0.0.1', 'timestamp': 1456603659,
        'has_dns': True, 'is_openresolver': True,
        'type': 'bind', 'version': '9.10.3-P2' }}
    
    get = odin_query.getall('1456603659')
    
    print(get)
    { 1456603659 : {'10.0.0.1' : { 'timestamp': 1456603659,
                    'has_dns': True, 'is_openresolver': True,
                    'type': 'bind', 'version': '9.10.3-P2' },
                    
                    '10.0.3.47': {'timestamp': 1456603659,
                    'has_dns': True, 'is_openresolver': False,
                    'type': False, 'version': False }
                    }}

    get = odin_query.getall('10.0.0.1')
    
    print(get)
    {1456603659 : {'10.0.0.1' : {'timestamp': 1456603659,
                    'has_dns': True, 'is_openresolver': True,
                    'type': 'bind', 'version': '9.10.3-P2' }},
                    
     1456602107 : {'10.0.0.1': {'timestamp': 1456602107,
                    'has_dns': True, 'is_openresolver': True,
                    'type': False, 'version': False }}
    }

### cli design

TODO
