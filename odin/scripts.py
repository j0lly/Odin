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

    # Dump sub parser
    dump = subparsers.add_parser('dump',)
    dump.add_argument("-o", "--output", dest="output", action="store",
                      help="Output file", required=True)

    # Load sub parser
    load = subparsers.add_parser('load',)
    load.add_argument("-i", "--input", dest="output", action="store",
                      help="Input file", required=True)

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
        pass

    # LOAD case
    elif args.subparser == "load":
        try:
            OpenDnsModel.load(args.input)
        except FileNotFoundError:
            print('{}{}{}'.format(
                '\nUnable to load data from',
                args.input,
                '. are you sure the file exisits?\n')
                 )

    # DUMP case
    elif args.subparser == "dump":
        if os.path.exists(args.output):
            answer = input(
                'file {} exist: overwrite? '.format(args.output))
            if answer in ['yes', 'y']:
                OpenDnsModel.dump(args.output)
            else:
                print('\nnot overwriting the file; print to stout only\n')
        else:
            OpenDnsModel.dump(args.output)

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

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
