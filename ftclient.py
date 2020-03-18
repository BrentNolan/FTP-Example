# Description:This is a client that connects with a companion FTP
#   server program. Once connected, it can request either a file listing
#   of the server's current directory or one-way transmission of a file from
#   server to client. The FTP session is managed over a control connection, and
#   the transmission of file information occurs over a separate data connection.

import os                       
import re                       
import sys                      
from socket import (            
    socket,
    gethostbyname,
    AF_INET,
    SOCK_STREAM,
    SOL_SOCKET,
    SO_REUSEADDR
)
from struct import pack, unpack 

BACKLOG = 5 # Arbitrary queue size for connection requests
TAG_LEN = 8 # Number of bytes reserved for tag field of packet header

def main():
    
    global serverHost
    global serverPort
    global command
    global filename
    global dataPort

    # Number of arguments error.
    if len(sys.argv) not in (5, 6):
        print (
            "usage: python2 ftclient <server-hostname> <server-port> " +
            "-l|-g [<filename>] <data-port>"
        )
        sys.exit(1)
    serverHost = gethostbyname(sys.argv[1])
    serverPort = sys.argv[2]
    command = sys.argv[3]
    filename = sys.argv[4] if len(sys.argv) == 6 else None
    dataPort = sys.argv[5] if len(sys.argv) == 6 else sys.argv[4]

    # -g (get) command error.
    if command == "-g" and filename is None:
        print (
            "usage: python2 ftclient <server-hostname> <server-port> " +
            "-l|-g [<filename>] <data-port>"
        )
        sys.exit(1)

    # Server integer error.
    if not isStrInt(serverPort):
        print "Client: Server port must be an integer"
        sys.exit(1)
    serverPort = int(serverPort)

    # Server port range error.
    if int(serverPort) < 1024 or int(serverPort) > 65535:
        print "Client: Server port must be in the range [1024, 65535]"
        sys.exit(1)

    # Command args error.
    if command not in ("-l", "-g"):
        print "Client: Command must be either -l or -g"
        sys.exit(1)

    #Data port integer error.
    if not isStrInt(dataPort):
        print "Client: Data port must be an integer"
        sys.exit(1)
    dataPort = int(dataPort)

    # Data port range error.
    if int(dataPort) < 1024 or int(dataPort) > 65535:
        print "Client: Data port must be in the range [1024, 65535]"
        sys.exit(1)

    # Server and data ports must be distinct error.
    if serverPort == dataPort:
        print "Client: Server port and data port cannot match"
        sys.exit(1)

    # Establish a control connection between the FTP client and server.
    startFtpClient()

    sys.exit(0)


# isStrInt
# Desc:  This function determines if the given string represents an integer.
# 
def isStrInt(string):
    # Attempt to match an integer substring.
    return re.match("^[0-9]+$", string) is not None


# recvAll
#
# Desc: Invokes "recv" as many times as necessary to receive
#       all of the given bytes of data.
#
# Rec: socket   - connection endpoint on which to receive data
#      numBytes - target number of bytes to receive
#
# Ret:  The buffer of received data is returned.

def recvAll(socket, numBytes):
    # Retrieve the given number of bytes.
    data = "";
    while len(data) < numBytes:
        try:
            data += socket.recv(numBytes - len(data))
        except Exception as e:
            print e.strerror
            sys.exit(1);

    return data


#recvPacket
#
#Desc:  This function receives a packet from the given socket.
#
#       The packet protocol is based on section 7.5 of Beej's Guide to
#       Network Programming.

# Rec: socket - connection endpoint on which to receive data
#
# Ret:  A (tag, data) tuple is returned.


def recvPacket(socket):
    # Receive the packet length.
    packetLength = unpack(">H", recvAll(socket, 2))[0]

    # Receive the tag field.
    tag = recvAll(socket, TAG_LEN).rstrip("\0")

    # Receive the encapsulated data.
    data = recvAll(socket, packetLength - TAG_LEN - 2)

    return tag, data


# runControlSession
#
# Desc:  Communicates with a server over an FTP control
#           connection.
#
# Rec: controlSocket - client-side endpoint of FTP control connection
#
# Ret:  -1 on error, 0 otherwise
 
def runControlSession(controlSocket):
    # Send given data port to the server.
    print "  Transmitting data port (FTP active mode) ..."
    outtag = "DPORT"
    outdata = str(dataPort)
    sendPacket(controlSocket, outtag, outdata)

    # Send given command to the server.
    print "  Transmitting command ..."
    outtag = "NULL"
    outdata = ""
    if command == "-l":
        outtag = "LIST"
    elif command == "-g":
        outtag = "GET"
        outdata = filename
    sendPacket(controlSocket, outtag, outdata)

    # Receive the server's response.
    intag, indata = recvPacket(controlSocket)

    # In the case of a server-side error, provide feedback for the user.
    if intag == "ERROR":
        print "Client: " + indata
        return -1
    return 0


# runDataSession
#
# Desc:  Transfers file information over an FTP data connection.
#
# Rec: controlSocket - client-side endpoint of FTP control connection
#      dataSocket    - client-side endpoint of FTP data connection
#
# Returns:  -1 on error, 0 otherwise
#

def runDataSession(controlSocket, dataSocket):
    ret = 0 # Return value

    # Retrieve the first packet from the server.
    intag, indata = recvPacket(dataSocket)

    # A list of filenames is being transferred.
    if intag == "FNAME":
        print "Client: File listing on \"{0}\"".format(serverHost, serverPort)

        # Print all received filenames.
        while intag != "DONE":
            print "  " + indata
            intag, indata = recvPacket(dataSocket)

    # A file is being transferred.
    elif intag == "FILE":
        # Don't allow files to be overwritten.
        filename = indata
        if os.path.exists(filename):
           print "Client: File \"{0}\" already exists".format(filename)
           ret = -1

        # Write the received data to file.
        else:
            with open(filename, "w") as outfile:
                while intag != "DONE":
                    intag, indata = recvPacket(dataSocket)
                    outfile.write(indata)
            print "Client: File transfer complete"

    # An error occurred.
    else:
        ret = -1

    # Acknowledge receipt of all packets.
    sendPacket(controlSocket, "ACK", "")

    return ret


# sendPacket
#
# Desc:  This function sends a packet from the given socket.
#
#        The packet protocol is based on section 7.5 of Beej's Guide to
#        Network Programming.
#                           
# Rec: socket - connection endpoint on which to send data
#           tag    - decorator for the encapsulated data
#           data   - information buffer to transfer
#
# Ret:  None

def sendPacket(socket, tag = "", data = ""):
    # Determine packet length.
    packetLength = 2 + TAG_LEN + len(data)

    # Build packet.
    packet = pack(">H", packetLength)
    packet += tag.ljust(TAG_LEN, "\0")
    packet += data

    # Send packet to the server.
    try:
        socket.sendall(packet)
    except Exception as e:
        print e.strerror
        sys.exit(1)


# startFtpClient
#
# Desc:  This function establishes an FTP control connection between the
#        client and given server.
#
# Rec: None
#
# Ret: None


def startFtpClient():
    # Create client-side endpoint of FTP control connection.
    try:
        controlSocket = socket(AF_INET, SOCK_STREAM, 0)
    except Exception as e:
        print e.strerror
        sys.exit(1)

    # Establish FTP control connection.
    try:
        controlSocket.connect((serverHost, serverPort))
    except Exception as e:
        print e.strerror
        sys.exit(1)
    print ("Client: FTP control connection established with " +
           "\"{0}\"".format(serverHost, serverPort)          )

    # Communicate over the control connection.
    status = runControlSession(controlSocket)

    # Accept FTP data services if control session was successful.
    if status != -1:
        # Create client-side socket.
        try:
            clientSocket = socket(AF_INET, SOCK_STREAM, 0)
        except Exception as e:
            print e.strerror
            sys.exit(1)

        # Associate client-side socket with given data port.
        try:
            clientSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
            clientSocket.bind(("", dataPort))
        except Exception as e:
            print e.strerror
            sys.exit(1)

        # Listen for connections.
        try:
            clientSocket.listen(BACKLOG)
        except Exception as e:
            print e.strerror
            sys.exit(1)

        # Establish FTP data connection.
        try:
            dataSocket = clientSocket.accept()[0]
        except Exception as e:
            print e.strerror
            sys.exit(1)
        print ("Client: FTP data connection established with " +
               "\"{0}\"".format(serverHost)                       )

        # Transfer file information over FTP data connection.
        runDataSession(controlSocket, dataSocket)

        # Display all queued error messages sent along control connection.
        while True:
            intag, indata = recvPacket(controlSocket)
            if intag == "ERROR":
                print "ftclient: " + indata
            if intag == "CLOSE":
                break

    # Close FTP control connection.
    try:
        controlSocket.close()
    except Exception as e:
        print e.strerror
        sys.exit(1)
    print "Client: FTP control connection closed"


# Define script point of entry.
if __name__ == "__main__":
    main()
