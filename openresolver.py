#!/usr/bin/env python

from Queue import Queue
import dns.resolver
import threading
import iptools
import sys



class thread_resolve (threading.Thread):

    def __init__(self, nameserver, q):
        threading.Thread.__init__(self)
        self.nameserver = nameserver
	self.q = q
    def run(self):
	resolve(self.nameserver, self.q)

def resolve(nameserver, q=None) :
	'''just resolve a well known dns query in order to check whetever the ip hosts an open resolver'''

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

        ### sanity checks ###
        if not iptools.ipv4.validate_ip(sys.argv[1]) and not iptools.ipv4.validate_cidr(sys.argv[1]):
                print 'not a valid ip or network -.- '
                sys.exit()
        if iptools.ipv4.validate_ip(sys.argv[1]) :
            for net in bad_networks:
                if sys.argv[1] in iptools.IpRange(net) :
                    print 'reserved ip, dumb!'
                    sys.exit()
        elif iptools.ipv4.validate_cidr(sys.argv[1]):
            for net in bad_networks:
                if iptools.IpRange(sys.argv[1]).__hash__() == iptools.IpRange(net).__hash__() :
                    print 'reserved network, dumb!'
                    sys.exit()

        if iptools.ipv4.validate_ip(sys.argv[1]) :
            resolve(sys.argv[1])

        else :

            # Get ip range mask
	    iprange = iptools.IpRange(sys.argv[1])

	    for ip_chunks in chunker(iprange, int(sys.argv[2])) :
                ### new dictionary and Queue ###
                threads = {}
	        queue = Queue()
                for ip in ip_chunks :
                    if ip is not None:
	                threads[ip] = thread_resolve(ip, queue)
	    	        threads[ip].start()

	        for thread in threads:
		    threads[thread].join()

	        try:
		    print queue.get_nowait()
	        except:
		    print "empty list: no resolvers :("

if __name__ == "__main__":
    main()
