OpenResolver: Open DNS Resolver crawler
===

This is a simple crawler that aim to surf the net and find open dns resolvers

## usage

    python openresolver.py [-h] -t TARGET [-c CHUNK] -o OUTPUT [-v]

    OpenResolver: an Open DNS Resolver crawler.

    optional arguments:
        -h, --help            show this help message and exit
        -t TARGET, --target TARGET
                        Set target: IP or CIDR range.
        -c CHUNK, --chunk CHUNK
                        Set Ip Range chunk size.
        -o OUTPUT, --output OUTPUT
                        Output file
        -v, --version         show program's version number and exit

##  Examples
        python openresolver.py -t 173.194.40.1 -o out.txt
        python openresolver.py -t 173.194.40.1/25 -c 50 -o results.txt 
        python openresolver.py -v
