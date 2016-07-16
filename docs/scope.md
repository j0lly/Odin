# Scope Doc

## Title

#### Odin

## Description

> Odin stand for Open Dns INspector; it born because of the lack of information
> about actual Open DNSs and their quantity/geographical location.
>
> Odin aims to scan the outside world looking for open resolver's Nameservers
> and store IP and others relevant data in a datastore for future statistical
> researches.
>
> Odin will be also able to continuosly monitor the actual data,
> with possibly more valuable information.

## Objectives

> Odin will provide a snapshot of DNS global situation (open resolvers) and
> as a valuable data to be used in statistical analysis. The tool will be
> also able to store data in an historical fashion.

### in scope

* provide a way to store DNS related data in a consistent way
* provide a method to retrive data from the datastore in a serialized way
* provide an api endpoint for data mining/quering
* provide a library for standard batch mining operations
* provide a methode to efficently query the Web without being hardly trottled
* provide a to run the same queries / scan from the termianl

### not in scope

* provide a way to graph the data collected
* a tool to scan the Web in 5 minutes

## Roadmap

    mvp
1. ship a simple miner module
2. ship a facade able to output data to stout, file or a datastore
3. ship an api
4. provides a service API for batch submission/data retrival
5. provides a cli for batch submission/data retrival
