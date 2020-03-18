Instructions:

1. Run ftserver on given port.

Run 'make' command in the directory with ftserver.c and the makefile to build the program.

Then run ftserver with the following command:
ftserver <server-port>

<server-port>:      port to bind with FTP control connection
                    endpoint; must be in range [1024, 65535]


Example:
make
ftserver 33444
ftserver: FTP server open on port 334444

					
2. Run ftclient by passing the IP address and port number of ftserver,
        list (-l) or get (-g) command, filename, and data port.


Run ftclient in the directory containing ftclient.py with the following command: 

python2 ftclient.py <server-hostname> <server-port> -l|-g [<filename>] <data-port>

<server-hostname>:  IP address of server (dotted-quad or domain name)

<server-port>:      port to bind with FTP control connection
                    endpoint; must be in range [1024, 65535]

-l|-g:              file listing (-l) or file transfer (-g) command

<filename>:         file to transfer from server to client

<data-port>:        port to bind with FTP data connection
                    endpoint; must be in range [1024, 65535]
		
Example:
python2 ftclient.py flip1 334444 -l 335555
<list of files in directory containing ftserver will be displayed>

python2 ftclient.py flip2 334444 -g <filename in server directory> 335555
<file wil be transfered to directory containing ftclient.py>
		
		
3. Repeat (2) for additional FTP requests, or send SIGINT to
        terminate ftserver.


Sources used
	Beej's Guide to Network Programming

        http://beej.us/guide/bgnet/output/html/multipage/index.html

    Python 2 API

        https://docs.python.org/2/library/socket.html
        https://docs.python.org/2/library/struct.html
        https://docs.python.org/2/library/stdtypes.html#bltin-file-objects

    Kurose & Ross
	
    Wikipedia - File Transfer Protocol

        https://en.wikipedia.org/wiki/File_Transfer_Protocol

    
   
