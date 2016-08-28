# -*- coding: utf-8 -*-

"""
Cli tool for odin
"""

import os
import argparse
import queue
from pprint import pprint
from odin.static import __version__
from odin.utils import run_scan
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
    parser.add_argument("-V", "--version", action="version",
                        version="%(prog)s " + __version__)
    subparsers = parser.add_subparsers(dest='subparser')

    # Scan sub parser
    scan = subparsers.add_parser('scan',
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
    scan.add_argument("-v", "--verbose", action="count")

    # Query sub parser
    query = subparsers.add_parser('query',)
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
    db = subparsers.add_parser('db',)
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
    delete = subparsers.add_parser('delete',)
    delete.add_argument("-t", "--target", dest="target",
                        action="store", type=str, default=None,
                        help="Set target for deletion: IP or CIDR range.",
                        required=True)

    return (parser.parse_args(), parser)


def test_args(args):
    """ test the passed arguments against sane values.

    :param args: argument passed to script
    :type args: argparse.Namespace
    :returns: list of ips, divided in chunks if necessary
    :rtype: list
    """

    targets = utils.findip(args.target)
    # assert len(targets) <= 256 or args.output
    # TODO tests on output file
    assert args.chunk > 1 and args.chunk <= 1024, (
        'You have to specify a chunk between 1 and 1024.')
    result = utils.chunker(targets, args.chunk)
    return result


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

    # SCAN case
    if args.subparser == "scan":
        targets = test_args(args)
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
            printing[obj.ip] = obj.serialize
            result.append(obj)

        if args.store:
            try:
                with OpenDnsModel.batch_write() as batch:
                    for ip in result:
                        batch.save(ip)
            except:
                print('batch failed to save to db')

        pprint(printing)

    # QUERY case
    elif args.subparser == "query":
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
        targets = utils.findip(args.target)
        # FIXME BUG in pynamo: single delete is ok, but batching complain about
        # key that cannnot be null
        objects = []
        for target in targets:
            try:
                objects.append(OpenDnsModel.get(target))
            # obj does not exist
            except:
                pass
        try:
            with OpenDnsModel.batch_write() as batch:
                for ip in objects:
                    batch.delete(ip)
        except Exception as err:
            print("unable to delete the specified ips: {}".format(err))

    # DB manipulation case
    elif args.subparser == "db":
        if args.describe:
            return pprint(OpenDnsModel.describe_table())

        if args.load:
            try:
                OpenDnsModel.load(args.load)
            except FileNotFoundError:
                print('{}{}{}'.format(
                    '\nUnable to load data from',
                    args.load,
                    '. are you sure the file exisits?\n')
                     )
                return
            return "data from '{}' succesfully loaded in DB".format(args.load)

        elif args.dump:
            if os.path.exists(args.dump):
                answer = input(
                    'file {} exist: overwrite? '.format(args.dump))
                if answer in ['yes', 'y']:
                    OpenDnsModel.dump(args.dump)
                else:
                    print('\nnot overwriting the file; print to stout only\n')
                    return
            else:
                OpenDnsModel.dump(args.dump)
            return "DB dumped correctly to {} file".format(args.dump)

        elif args.create:
            print("creating database... \n")
            try:
                read, write = (int(param) for param in args.create)
            except Exception as err:
                return "wrong read or write parameter specified: {}".format(
                        args.create)
            result = OpenDnsModel.create_table(wait=True,
                                               read_capacity_units=read,
                                               write_capacity_units=write)
            if result is None:
                print("DB already exist:\n")
                return pprint(OpenDnsModel.describe_table())
            else:
                return pprint(result)

        elif args.delete:
            print("deleting database.. \n")
            return OpenDnsModel.delete_table()

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
