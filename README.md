OpenResolver: Open DNS Resolver crawler
===

This is a simple crawler that aim to surf the net and find open dns resolvers

## usage

    python openresolver.py [Target] [Options] [Output]

    Target:
        -t, --target target       Target IP or Range (CIDR format)
    Options:
        -h, --help                Show basic help message
        -v, --version             Show program's version number
        -c, --chunk               Numer of IP Range's chunk to use
    Output: 
        -o, --output file         Print log on a file

    Examples:
        python openresolver.py -t 173.194.40.1
        python openresolver.py -t 173.194.40.1/25 -c 50 -o results.txt 
        python openresolver.py -v
