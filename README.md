Odin: Open Dns  INspector
===

[![Build Status](https://travis-ci.org/j0lly/Odin.svg?branch=master)](https://travis-ci.org/j0lly/Odin)

This is a simple Open DNS crawler that aim to surf the net and find open dns resolvers

The package include a cli for simple scans and a simple flask webapp; in both
cases the tool provides options to store the results into DynamoDB (also
locally) and retrieve aggregated / historical data.

The application is multi threaded: be wise when using 10k thread to spawn
connections into the wild :p

## Dependencies

Python 3.x

I'm too lazy to write what i can find already packaged :P
I've imported a couple of library that are not in the standard python libs:

* dnspython3
* iptools

## usage

    usage: openresolver.py [-h] -t TARGET [-c CHUNK] -o OUTPUT [-n HOSTNAME]
                       [-r DNS_TYPE] [-v]

    OpenResolver: an Open DNS Resolver crawler.

    optional arguments:

      -h, --help            show this help message and exit
      -t TARGET, --target TARGET
                            Set target: IP or CIDR range.
      -c CHUNK, --chunk CHUNK
                            Set Ip Range chunk size.
      -o OUTPUT, --output OUTPUT
                            Output file
      -n HOSTNAME, --name HOSTNAME
                            Hostname to resolve
      -r DNS_TYPE, --record DNS_TYPE
                            DNS query type
      -v, --version         show program's version number and exit

##  Examples

        python openresolver.py -t 173.194.40.1 -o out.txt
        python openresolver.py -t 173.194.40.1/25 -c 50 -o results.txt 
        python openresolver.py -t 173.194.40.1/29 -n www.google.com -r TXT  -o results.txt 
        python openresolver.py -v
