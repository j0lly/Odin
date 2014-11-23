#!/usr/bin/env python
# -*- coding: utf-8 -*-

# filename: openresolver.py
#
# author : j0lly [at] anche.no
# Open DNS Resolver crwaler
# For fun and profit
#
# Lcense BSD

from Queue import Queue
import dns.resolver
import threading
import iptools
import sys
import argparse

__version__ = '0.3'
__author__ = 'J0lly'
__date__ = '2014-11-23'
__email__ = 'j0lly@anche.no'

class thread_resolve (threading.Thread):

    def __init__(self, nameserver, q):
        threading.Thread.__init__(self)
        self.nameserver = nameserver
	self.q = q
    def run(self):
	resolve(self.nameserver, self.q)

def resolve(nameserver, q=None) :
	'''just resolve a well known dns query in order to check whetever the ip host is an open resolver'''

        # Set the DNS Server
	resolver = dns.resolver.Resolver()
	resolver.nameservers=[nameserver]
	resolver.timeout = 5
	resolver.lifetime = 5

	try:
	        print "resolving with %s"%(nameserver)
		for rdata in resolver.query('www.yahoo.com', 'CNAME') :
                        print rdata
    			print 'adding %s to the list'%(nameserver)
                        if q :
                            q.put(nameserver)
	except:
		pass

def chunker(iterable, chunksize):
        return map(None,*[iter(iterable)]*chunksize)

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
                        default="100", help="Set Ip Range chunk size.")
        parser.add_argument("-o", "--output", dest="output", action="store",
                        help="Output file", required=True)
        parser.add_argument('-v', '--version', action='version',
                                    version='%(prog)s ' + __version__)

        args = parser.parse_args()

        ### sanity checks ###
        if not iptools.ipv4.validate_ip(args.target) and not iptools.ipv4.validate_cidr(args.target):
                print 'not a valid ip or network -.- '
                sys.exit()
        if iptools.ipv4.validate_ip(args.target) :
            for net in bad_networks:
                if args.target in iptools.IpRange(net) :
                    print 'reserved ip, dumb!'
                    sys.exit()
        elif iptools.ipv4.validate_cidr(args.target):
            for net in bad_networks:
                if iptools.IpRange(args.target).__hash__() == iptools.IpRange(net).__hash__() :
                    print 'reserved network, dumb!'
                    sys.exit()

        ### real script ###
        if iptools.ipv4.validate_ip(args.target) :
            resolve(args.target)

        else :

            # Get ip range mask
	    iprange = iptools.IpRange(args.target)
	    queue = Queue()
	    resolvers = []

	    for ip_chunks in chunker(iprange, int(args.chunk)) :
                ### new dictionary and Queue ###
                threads = {}
                for ip in ip_chunks :
                    if ip is not None:
	                threads[ip] = thread_resolve(ip, queue)
	    	        threads[ip].start()

	        for thread in threads:
		    threads[thread].join()

		while queue.qsize() > 0:

		    resolvers.append(queue.get())
	    if resolvers :
	    	print 'I found %s resolvers!'%(len(resolvers))
                with open( args.output, 'w') as out_file:
                    out_file.write("\n".join(map(lambda x: str(x), resolvers)))
                    out_file.write("\n")
		print 'dumped list to %s '%(args.output)

if __name__ == "__main__":
    main()
