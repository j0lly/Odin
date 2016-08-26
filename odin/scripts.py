# -*- coding: utf-8 -*-

"""
Cli tool for odin
"""

import os
import argparse
import queue
import tempfile
from pprint import pprint
from odin.store import ThreadedModel
from odin.static import __version__
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
    scan.add_argument("-o", "--output", dest="output", action="store",
                      help="Output file", required=False)
    scan.add_argument("-f", "--filter", dest="filter", action="store",
                      help='{} {} {}'.format(
                          "show only if target is (or has):",
                          "is_dns, is_resolver, version, all.",
                          "It defaults to 'is_dns'."),
                      required=False, default='is_dns', type=str)
    scan.add_argument("-v", "--verbose", action="count")
    query = subparsers.add_parser('query',)
    query.add_argument("-t", "--target", dest="target",
                       action="store", type=str, default=None,
                       help="Set target: IP or CIDR range.", required=True)
    query.add_argument("-c", "--chunk", dest="chunk", action="store",
                       default=50, type=int,
                       help="Set Ip Range chunk size; 1024 max.")
    query.add_argument("-o", "--output", dest="output", action="store",
                       help="Output file", required=False)
    query.add_argument("-f", "--filter", dest="filter", action="store",
                       help='{} {} {}'.format(
                           "show only if target is (or has):",
                           "is_dns, is_resolver, version, all.",
                           "It defaults to 'is_dns'."),
                       required=False, default='is_dns', type=str)
    query.add_argument("-v", "--verbose", action="count")

    return parser.parse_args()


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
    if args.output:
        assert not os.path.isdir(
             args.output), 'specify a file, not a directory.'
        assert tempfile.TemporaryFile(dir=os.path.dirname(args.output)), (
            'You have no permission to write.')
    assert args.chunk > 1 and args.chunk <= 1024, (
        'You have to specify a chunk between 1 and 1024.')
    result = utils.chunker(targets, args.chunk)
    assert args.filter in ['is_dns', 'is_resolver', 'version', 'all'], (
        'You have to specify a filter in: is_dns, is_resolver, version, all.')

    return result


def run_query():
    """Run a query against the DB"""
    pass


def run_scan(args, queue, targets):
    """ Run a scan against targets and return a Pynamo modeled list of objects.
    :param args: arguments from main
    :type args: argparse.Namespace
    :queue: a queue passed here from main
    :type queue: queue.Queue
    :param targets: list of ips, divided in chunks if necessary
    :type targets: list
    :returns: a dict of pynamo objects, and the ip as the key
    :rtype: dict
    """

    result = {}

    for chunk in targets:
        threads = []
        for ip in chunk:
            obj = ThreadedModel(ip, queue=queue)
            obj.daemon = True
            threads.append(obj)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=2)

        while not queue.empty():
            ip_info = queue.get()
            if args.filter == 'all':
                result.update({ip_info.ip: ip_info.serialize})
            elif getattr(ip_info, args.filter):
                result.update({ip_info.ip: ip_info.serialize})
    if args.output:
        if os.path.exists(args.output):
            answer = input('file {} exist: overwrite? '.format(args.output))
            if answer in ['yes', 'y']:
                with open(args.output, 'w') as output:
                    output.write(str(result))
            else:
                print('\nnot overwriting the file; print to stout only\n')

    return result


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

    args = get_args()

    if args.subparser == "scan":
        targets = test_args(args)
        my_queue = queue.Queue()
        result = run_scan(args, my_queue, targets)

    elif args.subparser == "query":
        pass

    pprint(result)


if __name__ == "__main__":
    main()
