# -*- coding: utf-8 -*-

"""
Cli tool for odin
"""

import os
import argparse
import queue
from pprint import pprint
from odin.store import ThreadedModel
from odin.static import __version__
from odin import utils


def get_args():
    """ parse input. """

    parser = argparse.ArgumentParser(
        description='OpenResolver: an Open DNS Resolver crawler.')
    parser.add_argument("-t", "--target", dest="target", action="store", type=str,
                        default=None, help="Set target: IP or CIDR range.", required=True)
    parser.add_argument("-c", "--chunk", dest="chunk", action="store",
                        default=50, help="Set Ip Range chunk size; 1024 max.")
    parser.add_argument("-o", "--output", dest="output", action="store",
                        help="Output file", required=False)
    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s ' + __version__)

    return parser.parse_args()

def test_args(args):
    """ test the passed arguments against sane values.

    :param args: argument passed to script
    :type args: argparse.Namespace
    :returns: list of ips, divided in chunks if necessary
    :rtype: list
    """

    targets = utils.findip(args.target)
    assert len(targets) <= 256 or args.output
    #TODO tests on output file
    output = os.path.abspath(args.output)
    assert not os.path.exists(output)
    assert args.chunk > 1 and args.chunk <= 1024
    result = utils.chunker(targets, args.chunk)
    return result



def main():
    """ the main script. """
    args = get_args()

    targets = test_args(args)

    threads = []
    result = {}
    my_queue = queue.Queue()

    for chunk in targets:
        for ip in chunk:
            obj = ThreadedModel(ip, queue=my_queue)
            obj.daemon = True
            threads.append(obj)
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=4)

        while not my_queue.empty():
            ip_info = my_queue.get()
            result.update({ip_info['ip'] : ip_info})
    pprint(result)




if __name__ == "__main__":
    main()
