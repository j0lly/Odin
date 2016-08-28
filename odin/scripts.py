# -*- coding: utf-8 -*-

"""
Cli tool for odin
"""

import os
import argparse
import queue
import logging
from pprint import pprint
from odin.static import __version__
from odin.utils import run_scan, get_logger
from odin.store import OpenDnsModel
from odin import utils


def get_args():
    """Parse input parameters

    :returns: an Namespace object with inputted arguments
    :rtype: argparse.Namespace
    """

    parser = argparse.ArgumentParser(
        description='{0}{1}{2}{3}{4}{5}{6}'.format(
            'Odin is a command line tool to scan an host or a ',
            'CIDR formatted network and find Open Resolvers. ',
            'As you would probably run the script over some 1000~ hosts at ',
            'a time, the chuck switch is provided in order to select the ',
            'thread pool number to spawn to process the requests. (bare in ',
            'mind your ISP could easely throttle you out if you burst to much',
            'traffic in a single run!)'))
    parser_exclusive = parser.add_mutually_exclusive_group(required=False)
    parser_exclusive.add_argument('-v', '--verbose',
                                  action='count', default=None)
    parser_exclusive.add_argument('-q', '--quiet',
                                  action='store_const', const=0, default=None)
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s " + __version__)

    hold_parser = argparse.ArgumentParser(add_help=False)
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
    query.add_argument("-t", "--target", dest="target",
                       action="store", type=str, default=None,
                       help="Set target: IP or CIDR range.", required=True)
    query.add_argument("-c", "--chunk", dest="chunk", action="store",
                       default=50, type=int,
                       help="Set Ip Range chunk size; 1024 max.")
    query.add_argument("-f", "--filter", dest="filter", action="store",
                       help='{} {} {}'.format(
                           "show only if target is (or has):",
                           "is_dns, is_resolver, version, all.",
                           "It defaults to 'is_resolver'."),
                       required=False, default='is_resolver', type=str)

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


def run_query():
    """Run a query against the DB"""
    pass


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
    log = get_logger(level)

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
        pass

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

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
