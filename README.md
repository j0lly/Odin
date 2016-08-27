Odin: Open Dns  INspector
===

[![Build Status](https://travis-ci.org/j0lly/Odin.svg?branch=master)](https://travis-ci.org/j0lly/Odin)
[![Coverage Status](https://coveralls.io/repos/github/j0lly/Odin/badge.svg?branch=master)](https://coveralls.io/github/j0lly/Odin?branch=master)

This is a simple Open DNS crawler that aim to surf the net and find open dns resolvers

The package include a cli for simple scans and queries plus some helpers to
manipulate the dataset.
The package provides also a Flask webapp; in both
cases the tool provides options to store the results into DynamoDB (also
locally) and retrieve aggregated / historical data.

The application is multi threaded: be wise when using 10k threads to spawn
connections into the wild :p

## Why

* I was bored
* I was interested in DDOS amplification attacks
* I was curious about how many Open resolvers are out there still in 2016
* I was going to learn Flask and DynamoDB technologies

## Installation

```sh
git clone https://github.com/j0lly/Odin.git
pip install Odin/ -r Odin/requirements.txt
```


## Usage

    usage: odin scan [-h] -t TARGET [-c CHUNK] -o OUTPUT [-n HOSTNAME]
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

## Examples

        odin scan -t 173.194.40.1 --store
        odin scan -t 173.194.40.1/25 -c 50 -f all --store results.txt
        odin load -F other_results.txt
        odin query --help
