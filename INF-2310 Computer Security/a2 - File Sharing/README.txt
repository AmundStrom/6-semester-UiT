How to run, go to /src:

1. Run <python ftserv.py serverData.txt>.
   It will print the hostname to be used for the client.

2. Run <python ftclient.py "hostname">, 
   with the hostname given by ftserv.py.


This should generate in total 3 new files in the current directory:
    - 2 files which contain the private and public key of the server.
    - 1 file which is the data the client received from the server.