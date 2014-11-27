#!/usr/bin/env python
# -*- coding: utf-8 -*-

# filename: openresolver.py
#
# author : j0lly [at] anche.no
# Open DNS Resolver crwaler
# For fun and profit
#
# Lcense BSD

from queue import Queue
import dns.resolver
import threading
import iptools
import sys
import argparse

__version__ = '1.0'
__author__ = 'J0lly'
__date__ = '2014-11-27'
__email__ = 'j0lly@anche.no'

class thread_resolve(threading.Thread):

    def __init__(self, nameserver, q, hostname, dns_type):
        threading.Thread.__init__(self)
        self.nameserver = nameserver
        self.q = q
        self.hostname = hostname
        self.dns_type = dns_type
    def run(self):
        resolve(self.nameserver, self.q, self.hostname, self.dns_type)

def resolve(nameserver, q, hostname, dns_record) :
    '''just resolve a well known dns query in order to check whetever the ip host is an open resolver'''

        # Set the DNS Server
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [nameserver]
    resolver.timeout = 5
    resolver.lifetime = 5
    print("resolving with %s"%(nameserver))

    try:
        rdata = resolver.query(hostname, dns_record)

    except dns.resolver.NoAnswer :
        print('no resolver for %s'%(nameserver))
        sys.exit()
    except dns.rdatatype.UnknownRdatatype :
        print('bad Record Type %s'%(dns_record))
        sys.exit()
    except dns.resolver.NXDOMAIN :
        print('%s is not existent'%(hostname))
        sys.exit()
    except dns.exception.Timeout :
        print('timeout while performing query on %s'%(nameserver))
        sys.exit()
    except :
        print('Unknown error')
        sys.exit()

        #rdata.response for complete response body
        print('we can resolve %s'%(hostname))
        print('adding %s to the list'%(nameserver))
        q.put(nameserver)

def chunker(iterable, chunksize):
    return  [iterable[x:x+chunksize] for x in  range(0, len(iterable), chunksize)]

def main():

        bad_networks = [ iptools.ipv4.PRIVATE_NETWORK_10, iptools.ipv4.LOOPBACK,
                        iptools.ipv4.LINK_LOCAL, iptools.ipv4.IPV6_TO_IPV4_RELAY,
                        iptools.ipv4.CURRENT_NETWORK, iptools.ipv4.DUAL_STACK_LITE,
                        iptools.ipv4.MULTICAST, iptools.ipv4.MULTICAST_INTERNETWORK,
                        iptools.ipv4.MULTICAST_LOCAL, iptools.ipv4.PRIVATE_NETWORK_172_16,
                        iptools.ipv4.PRIVATE_NETWORK_192_168, iptools.ipv4.RESERVED
                        ]

        parser = argparse.ArgumentParser(description='OpenResolver: an Open DNS Resolver crawler.')
        parser.add_argument("-t", "--target", dest="target", action="store", type=str,
                default=None, help="Set target: IP or CIDR range.", required=True)
        parser.add_argument("-c", "--chunk", dest="chunk", action="store",
                        default=50, help="Set Ip Range chunk size.")
        parser.add_argument("-o", "--output", dest="output", action="store",
                        help="Output file", required=True)
        parser.add_argument("-n", "--name", dest="hostname", default="www.yahoo.com", action="store",
                        help="Hostname to resolve" )
        parser.add_argument("-r", "--record", dest="dns_type", default="CNAME", action="store",
                        help="DNS query type")
        parser.add_argument('-v', '--version', action='version',
                                    version='%(prog)s ' + __version__)

        args = parser.parse_args()
        chunks = args.chunk

        ### sanity checks ###
        if not iptools.ipv4.validate_ip(args.target) and not iptools.ipv4.validate_cidr(args.target):
                print('not a valid ip or network')
                sys.exit()
        if iptools.ipv4.validate_ip(args.target) :
            for net in bad_networks:
                if args.target in iptools.IpRange(net) :
                    print('reserved ip! please, select a real Ip instead try to flood your network!')
                    sys.exit()
        elif iptools.ipv4.validate_cidr(args.target):
            for net in bad_networks:
                if iptools.IpRange(args.target).__hash__() == iptools.IpRange(net).__hash__() :
                    print('reserved network! please, select a real Ip instead try to flood your network!')
                    sys.exit()
        if chunks > len(iptools.IpRange(args.target)) :
            print('chunk too big for the Ip range provoded: %s \nadjusting to minimum: %s'%(chunks, len(iptools.IpRange(args.target))))
            chunks = len(iptools.IpRange(args.target))

        ###################
        ### real script ###
        ###################

        # Get ip range mask
        iprange = iptools.IpRange(args.target)
        queue = Queue()
        resolvers = []

        for ip_chunks in chunker(iprange, int(chunks)) :
                ### new dictionary and Queue ###
                threads = {}
                for ip in ip_chunks :
                    if ip is not None:
                        threads[ip] = thread_resolve(ip, queue, args.hostname, args.dns_type)
                        threads[ip].start()

                for thread in threads:
                    threads[thread].join()

        ### getting results from piped threads ###
        while queue.qsize() > 0:

            resolvers.append(queue.get())

        ### if we found any open resolver, put it to the right output media ###
        if resolvers :
            print('I found %s resolvers!'%(len(resolvers)))
            with open( args.output, 'w') as out_file:
                out_file.write("\n".join([str(x) for x in resolvers]))
                out_file.write("\n")
            print('dumped list to %s '%(args.output))
        else:
            print('No DNS found :(')

if __name__ == "__main__":
        main()
