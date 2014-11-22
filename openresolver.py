#!/usr/bin/env python2

#import socket
import dns.resolver
import thread
import threading
import iptools
import sys
from Queue import Queue



class thread_resolve (threading.Thread):
#'''just resolve a well known dns query in order to check whetever the ip hosts an open resolver'''

    def __init__(self, nameserver, q):
        threading.Thread.__init__(self)
        self.nameserver = nameserver
	self.q = q
    def run(self):
	resolve(self.nameserver, self.q)

def resolve(nameserver, q) :
	'''just resolve a well known dns query in order to check whetever the ip hosts an open resolver'''
	# Set the DNS Server
	resolver = dns.resolver.Resolver()
	resolver.nameservers=[nameserver]
	resolver.timeout = 5
	resolver.lifetime = 5

	print "resolving with %s"%(nameserver)
	try:
		for rdata in resolver.query('www.yahoo.com', 'CNAME') :
                        print rdata
    			print 'adding %s to the list'%(nameserver)
			q.put(nameserver)
	except:
		pass

def main():

	queue = Queue()
	# Get ip range mask
	iprange = iptools.IpRangeList(sys.argv[1])
	threads = {}

	for ip in iprange:
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
