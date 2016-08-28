# -*- coding: utf-8 -*-

"""
Cli tool for odin
"""

import os
import argparse
import queue
import logging
from pprint import pprint
import odin
from odin.static import __version__
from odin.utils import (run_scan, assembler, get_filter)
from odin.store import OpenDnsModel
from odin import utils

# Default logging capabilities (logging nowhere)
log = odin.get_logger()


def get_args():
    """Parse input parameters

    :returns: an Namespace object with inputted arguments
    :rtype: argparse.Namespace
    """

    parser = argparse.ArgumentParser()
    parser_exclusive = parser.add_mutually_exclusive_group(required=False)
    parser_exclusive.add_argument('-v', '--verbose',
                                  action='count', default=None)
    parser_exclusive.add_argument('-q', '--quiet',
                                  action='store_const', const=0, default=None)

    hold_parser = argparse.ArgumentParser(
        description='{0}{1}{2}{3}{4}{5}{6}'.format(
            'Odin is a command line tool to scan an host or a ',
            'CIDR formatted network and find Open Resolvers. ',
            'As you would probably run the script over some 1000~ hosts at ',
            'a time, the chuck switch is provided in order to select the ',
            'thread pool number to spawn to process the requests. (bare in ',
            'mind your ISP could easely throttle you out if you burst to much',
            'traffic in a single run!)'))
    hold_parser.add_argument("--version", action="version",
                             version="%(prog)s " + __version__)
    subparsers = hold_parser.add_subparsers(dest="subparser")

    # Scan sub parser
    scan = subparsers.add_parser('scan', parents=[parser],
                                 conflict_handler='resolve',
                                 description="{}{}{}".format(
                                     "Perform a scan and return the ",
                                     "result, optionally save the ",
                                     "scan into the DB"))
    scan.add_argument("-t", "--target", dest="target",
                      action="store", type=str, default=None,
                      help="Set target: IP or CIDR range.", required=True)
    scan.add_argument("-c", "--chunk", dest="chunk", action="store",
                      default=50, type=int,
                      help="Set Ip Range chunk size; 1024 max.")
    scan.add_argument("-f", "--filter", dest="filter", action="store",
                      help='{} {} {}'.format(
                          "show only if target is (or has):",
                          "is_dns, is_resolver, version, all.",
                          "It defaults to 'is_dns'."),
                      required=False, default='is_resolver', type=str)
    scan.add_argument("--store", action="store_true",
                      help="if specified store the result in Dynamo")

    # Query sub parser
    query = subparsers.add_parser('query', parents=[parser],
                                  conflict_handler='resolve',
                                  )
    query.add_argument("-t", "--type", dest="type",
                       action="store", type=str,
                       required=True, help="{}{}".format(
                           "Specify the type of record to query for: ",
                           "is_dns | is_resolver"))
    query.add_argument("-r", "--range", dest="range",
                       action="store", type=str, default=None,
                       help="{}{}".format(
                           "Set target range in the form like: ",
                           "192 | 192.168 | 192.168.0"))
    query.add_argument("-V", "--version", dest="version", nargs='?',
                       const=None, type=str,
                       help='{} {} {}'.format(
                           "query only for target with ",
                           "or without a particular dns version in the form:",
                           "'dnsmasq' or '!dnsmasq'"))
    query.add_argument("--reversed", action="store_false",
                       help="{}{}".format(
                           "if specified, the resultset ",
                           "is sorted from older to newer"),
                       default=True)
    query.add_argument("-l", "--limit", dest="limit", action="store",
                       default=None, type=int,
                       help="Set a limit for results")

    # Db sun parser
    db = subparsers.add_parser('db', parents=[parser],
                               conflict_handler='resolve',
                               )
    exclusive = db.add_mutually_exclusive_group(required=True)
    exclusive.add_argument("--dump", dest="dump", action="store",
                           help="Output file")
    exclusive.add_argument("--load", dest="load", action="store",
                           help="Input file")
    exclusive.add_argument("--create", dest="create",
                           nargs=2, metavar=('read', 'write'),
                           help="{}{}".format(
                               "Create the DB, if not exists already,",
                               " giving read and write capacity"))
    exclusive.add_argument("--delete", action="store_true",
                           help="delete the DB table")
    exclusive.add_argument("--describe", action="store_true",
                           help="describe the DB tables")

    # Delete sub parser
    delete = subparsers.add_parser('delete', parents=[parser],
                                   conflict_handler='resolve'
                                   )
    delete.add_argument("-t", "--target", dest="target",
                        action="store", type=str, default=None,
                        help="Set target for deletion: IP or CIDR range.",
                        required=True)

    return (hold_parser.parse_args(), hold_parser)


def do_query(subject, index=None,
             nets=[], scan_index_forward=None, limit=None,
             version_string=None, negate_version=None):
    """Run a query against the DB"""

    if negate_version:
        version_name = 'version__not_contains'
    elif version_string is True:
        version_name = 'version__not_null'
    else:
        version_name = 'version__contains'

    query = {'scan_index_forward': scan_index_forward}
    if limit is not None:
        query.update({'limit': limit})
    if version_string:
        query.update({version_name: version_string})

    if subject == 'is_resolver':
        query_over = getattr(OpenDnsModel, 'openresolvers_index')
    elif subject == 'is_dns':
        query_over = getattr(OpenDnsModel, 'dns_index')
        query.update({'is_resolver__eq': False,
                      'is_dns__eq': True})  # FIXME

    if len(nets) is 0:
        log.info('performing a single query for %s type', subject)
        for ip in query_over.query(1, **query,):
            log.debug('returned ip: %s', ip.ip)
            yield ip
    else:
        log.info('performing a batch of queries for %s type', subject)
        for net in nets:
            log.debug('query for net: %s', net)
            query.update({index + '__eq': str(net)})
            for ip in query_over.query(1, **query,):
                log.debug('returned ip: %s', ip.ip)
                yield ip


def load_data():
    """ load data into the DB; can get data from file
    data has to be formatted as json with the following syntax:
        {'192.168.0.1': { 'ip': '192.168.0.1',
                          'is_dns': True,
                          'is_resolver': True,
                          'netmask': '192.168',
                          'timestamp': ###,
                          'version': 'dnsmasq-2.70'
                        }
        }
    """
    pass


def main():
    """ the main script."""

    args, parser = get_args()
    if args.subparser is None:
        parser.print_help()
        return

    # setup logging
    levels = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]
    # taking care to check either verbosity or quiet flag
    if args.verbose is not None:
        arg = args.verbose + 1
    elif args.quiet is not None:
        arg = args.quiet
    else:
        arg = 1
    level = levels[min(len(levels)-1, arg)]
    log = odin.get_logger(level)

    # SCAN case
    if args.subparser == "scan":
        log.info('Preparing for scanning..')

        targets = utils.findip(args.target)
        log.debug('list of ip to be scanned: %s', targets)

        assert args.chunk > 1 and args.chunk <= 1024, (
            'You have to specify a chunk between 1 and 1024.')
        targets = utils.chunker(targets, args.chunk)

        assert args.filter in ['is_dns',
                               'is_resolver',
                               'version',
                               'all'], ('{}{}'.format(
                                   'You have to specify a filter in:',
                                   ' is_dns, is_resolver, version, all.'))

        my_queue = queue.Queue()
        result = []
        printing = {}

        for obj in run_scan(args.filter, my_queue, targets):
            log.debug('adding %s to the resultset', obj.ip)
            printing[obj.ip] = obj.serialize
            result.append(obj)

        if args.store:
            log.info('store flag passed: saving results into the DB..')
            try:
                with OpenDnsModel.batch_write() as batch:
                    for ip in result:
                        log.debug('storing ip: %s', ip)
                        batch.save(ip)
            except Exception as err:
                log.error('batch failed to save to db:', exc_info=True)
                pass

        pprint(printing)

    # QUERY case
    elif args.subparser == "query":
        log.info('Preparing for querying..')
        # query needs:
        # * show all openresolvers
        # * show all openresolvers with version X
        # * show all dns
        # * show all dns with version X
        # * show all
        # - all above with given range 192, 192.168, 192.168.55
        # - all above with timerange first to last or viceversa
        # - all above with filter option to show only certain info
        # * show last X [anythig, dns, resolver], with possible cass filter
        # * count number per: all, dns, resolver, with  possible class fliter
        if args.range:
            cidr, class_range = assembler(args.range)
            nets = [args.range]
        else:
            class_range = None
            nets = []

        if args.version == 1:
            version_string, negate_version = True, None
        elif args.version:
            version_string, negate_version = get_filter(args.version)
        else:
            version_string, negate_version = None, None
        log.debug(
            'cheking version params: version_string %s, negate_version %s',
            version_string, negate_version)

        for i in do_query(args.type, index=class_range,
                          nets=nets, scan_index_forward=args.reversed,
                          version_string=version_string, limit=args.limit,
                          negate_version=negate_version):
            log.debug('perform serialization of obj: %s', i.ip)
            pprint(i.serialize)

    # DELETE CASE
    elif args.subparser == "delete":
        log.info('starting deletion of IP addresses')
        targets = utils.findip(args.target)
        # FIXME BUG in pynamo: single delete is ok, but batching complain about
        # key that cannnot be null
        objects = []
        for target in targets:
            log.debug('preparing to delete item: %s', target)
            try:
                objects.append(OpenDnsModel.get(target))
            # obj does not exist
            except Exception as err:
                log.info('ip: %s does not exist in DB', target)
        try:
            with OpenDnsModel.batch_write() as batch:
                for ip in objects:
                    batch.delete(ip)
        except Exception as err:
            log.error("unable to delete the specified ips: %s",
                      err, exc_info=True)
            return
        log.info('delete operation finished successfully')

    # DB manipulation case
    elif args.subparser == "db":
        if args.describe:
            log.info('describe table %s', OpenDnsModel.Meta.table_name)
            return pprint(OpenDnsModel.describe_table())

        if args.load:
            log.info('preparing to load dataset from file..')
            try:
                OpenDnsModel.load(args.load)
            except FileNotFoundError as err:
                log.fatal('%s%s%s',
                          '\nUnable to load data from',
                          args.load,
                          '. are you sure the file exisits?\n')
                return
            log.info('data succefully loaded from %s', args.load)

        elif args.dump:
            log.info('dumping the DB in %s', args.dump)
            if os.path.exists(args.dump):
                answer = input(
                    'file {} exist: overwrite? '.format(args.dump))
                if answer in ['yes', 'y']:
                    OpenDnsModel.dump(args.dump)
                else:
                    log.warn('user choice exception, exiting..')
            else:
                OpenDnsModel.dump(args.dump)
            log.info('DB dumped correctly')

        elif args.create:
            log.info("creating database... ")
            try:
                read, write = (int(param) for param in args.create)
            except Exception as err:
                log.fatal(
                    'wrong read or write parameter specified: %s',
                    args.create)
                return

            result = OpenDnsModel.create_table(wait=True,
                                               read_capacity_units=read,
                                               write_capacity_units=write)
            if result is None:
                log.debug('DB already exist')
                return pprint(OpenDnsModel.describe_table())
            else:
                return pprint(result)

        elif args.delete:
            log.info("deleting database.. ")
            result = OpenDnsModel.delete_table()
            log.info("delete successful")
            return pprint(result)

        elif args.modify:
            # TODO mafe a function I saved output because no documentation is
            # there
            # q=TableConnection(table_name='OpenDns',
            #         host='http://127.0.0.1:8000')
            # q.update_table(
            #         read_capacity_units=50,
            #         write_capacity_units=50,
            #         global_secondary_index_updates=[
            #             {'read_capacity_units': 50,
            #              'write_capacity_units': 50,
            #              'index_name': 'ClassA'}])
            pass

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
