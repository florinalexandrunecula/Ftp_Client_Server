import socket
import sys
import time
import os
import struct

from _thread import *


print("\nWelcome to the FTP server.\n\nTo get started, connect a client.")

HOST = "127.0.0.1"
PORT = 1456
BUFFER_SIZE = 1024


def upload(conn):
    """
    Receive the file from the client
    :param conn: Connection to the client
    :return:
    """
    conn.send("1".encode('utf-8'))
    file_name_size = struct.unpack("h", conn.recv(2))[0]
    file_name = conn.recv(file_name_size).decode('utf-8')
    conn.send("1".encode('utf-8'))
    file_size = struct.unpack("i", conn.recv(4))[0]
    start_time = time.time()
    output_file = open(file_name, "wb")
    bytes_received = 0
    print("\nReceiving...")
    while bytes_received < file_size:
        l = conn.recv(BUFFER_SIZE)
        output_file.write(l)
        bytes_received += BUFFER_SIZE
    output_file.close()
    print(f"\nReceived file: {file_name}")
    conn.send(struct.pack("f", time.time() - start_time))
    conn.send(struct.pack("i", file_size))
    return


def list_files(conn):
    """
    List all the files present in the script directory
    :param conn: Connection to the client
    :return:
    """
    print("Listing files...")
    listing = os.listdir(os.getcwd())
    conn.send(struct.pack("i", len(listing)))
    total_directory_size = 0
    for i in listing:
        conn.send(struct.pack("i", sys.getsizeof(i)))
        conn.send(i.encode('utf-8'))
        conn.send(struct.pack("i", os.path.getsize(i)))
        total_directory_size += os.path.getsize(i)
        conn.recv(BUFFER_SIZE)
    conn.send(struct.pack("i", total_directory_size))
    conn.recv(BUFFER_SIZE)
    print("Successfully sent file listing")
    return


def download(conn):
    """
    Send the requested file to the client
    :param conn: Connection to the client
    :return:
    """
    conn.send("1".encode('utf-8'))
    file_name_length = struct.unpack("h", conn.recv(2))[0]
    print(file_name_length)
    file_name = conn.recv(file_name_length).decode('utf-8')
    print(file_name)
    if os.path.isfile(file_name):
        conn.send(struct.pack("i", os.path.getsize(file_name)))
    else:
        print("File name not valid")
        conn.send(struct.pack("i", -1))
        return
    conn.recv(BUFFER_SIZE)
    start_time = time.time()
    print("Sending file...")
    content = open(file_name, "rb")
    l = content.read(BUFFER_SIZE)
    while l:
        conn.send(l)
        l = content.read(BUFFER_SIZE)
    content.close()
    conn.recv(BUFFER_SIZE)
    conn.send(struct.pack("f", time.time() - start_time))
    return


def delete(conn):
    """
    Delete file specified by client
    :param conn: Connection to client
    :return:
    """
    conn.send("1".encode('utf-8'))
    file_name_length = struct.unpack("h", conn.recv(2))[0]
    file_name = conn.recv(file_name_length).decode('utf-8')
    if os.path.isfile(file_name):
        conn.send(struct.pack("i", 1))
    else:
        conn.send(struct.pack("i", -1))
    confirm_delete = conn.recv(BUFFER_SIZE).decode('utf-8')
    if confirm_delete == "Y":
        try:
            os.remove(file_name)
            conn.send(struct.pack("i", 1))
        except:
            print(f"Failed to delete {file_name}")
            conn.send(struct.pack("i", -1))
    else:
        print("Delete abandoned by client!")
        return


def quit(conn):
    """
    Close the connection to the client
    :param conn: Connection to client
    :return:
    """
    conn.close()


def threaded(conn, addr):
    """
    The function that will be run on multiple threads.
    All the client commands are processed here.
    :param conn: Connection to client
    :param addr: The client address (ip, port)
    :return:
    """
    while True:
        print("\n\nWaiting for instruction")
        data = conn.recv(BUFFER_SIZE).decode('utf-8')
        print(f"\nRecieved instruction: {data}")
        if data == "UPLD":
            upload(conn)
        elif data == "LIST":
            list_files(conn)
        elif data == "DWLD":
            download(conn)
        elif data == "DELF":
            delete(conn)
        elif data == "QUIT":
            quit(conn)
            print(f"Disconnected from {addr}")
            break
        data = None


def main():
    """
    Main function that initialises the socket and binds it to the ip and port mentioned above
    :return:
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(1)

    while True:
        conn, addr = s.accept()

        print(f"Connected to {addr}")

        start_new_thread(threaded, (conn, addr))

    s.close()


if __name__ == "__main__":
    main()
