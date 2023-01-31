# What is here

1. a filtering "replay" script, `playback.py`. This reads a log file, parses the header, and transmits data into a file (or serial port-like object). Filtering is selective on the accelerometer indices. Currently the implementation allows selection for `--row top` or `--row bottom`.  Editing the list in the code is straightforward.

2. a pyqtgraph-based rendering tool, `rendr.py`. This reads a serial port, and plots lines as soon as possible in a multi-line Qt plot. Filtering is done as per the `playback` script (--row argument).

# How to run

`python3 rendr.py -p /dev/ttyACM1 -b 5000 --protocol 2 -d 30 --row top`




# How to test

- generate a fake socket (pseudo-terminal):
`socat -d -d pty,raw,echo=0 pty,raw,echo=0`
- note the output
e.g. 
```
2022/06/21 22:18:15 socat[26264] N PTY is /dev/pts/9
2022/06/21 22:18:15 socat[26264] N PTY is /dev/pts/10

```

the two ends of the socket are /dev/pts/9 and /10.
you can attach either program to either end of the socket.

- put data playback down one end of the socket
`python3 playback.py -n 3000 -d 0.01 -p /dev/pts/9 -i log.txt --protocol 2`

where arguments are:

`-d <delay between sending lines>`
`-p <port>`
`--protocol 2` (default; emit entire lines, not a subset)


- consume the data and plot it
`python3 rendr.py -p /dev/pts/10 -b 5000 --protocol 2 -d 30`


where arguments are:

`-d <delay between updating graph, in counts of incoming data points>`
`-p <port>`
`--protocol 2` (default; expect entire lines, not a subset)
`-b <buffer length>` 





# Dependencies

* Qt5
* pyqgraphqt
* python-qt bindings
* python-numpy

