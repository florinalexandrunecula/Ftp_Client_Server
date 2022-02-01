import sys
import os
import struct

from socket import AF_INET, SOCK_STREAM, socket


HOST = "127.0.0.1"
PORT = 12000
BUFFER_SIZE = 1024
sock = socket(AF_INET, SOCK_STREAM)


def connect():
    """
    Connect to the server
    :return:
    """
    print("Sending server request...")
    try:
        sock.connect((HOST, PORT))
        print("Connection successful")
    except:
        print("Connection unsuccessful. Make sure the server is online.")


def upload(file_name):
    """
    Upload a file to the server
    :param file_name: name of the file that will be uploaded
    :return:
    """
    print(f"\nUploading file: {file_name}...")
    try:
        content = open(file_name, "rb")
    except:
        print("Couldn't open file. Make sure the file name was entered correctly.")
        return
    try:
        sock.send("UPLD".encode('utf-8'))
    except:
        print("Couldn't make server request. Make sure a connection has bene established.")
        return
    try:
        sock.recv(BUFFER_SIZE)
        sock.send(struct.pack("h", sys.getsizeof(file_name)))
        sock.send(file_name.encode('utf-8'))
        sock.recv(BUFFER_SIZE)
        sock.send(struct.pack("i", os.path.getsize(file_name)))
    except:
        print("Error sending file details")
    try:
        l = content.read(BUFFER_SIZE)
        print("\nSending...")
        while l:
            sock.send(l)
            l = content.read(BUFFER_SIZE)
        content.close()
        upload_time = struct.unpack("f", sock.recv(4))[0]
        upload_size = struct.unpack("i", sock.recv(4))[0]
        print(f"\nSent file: {file_name}\nTime elapsed: {upload_time}s\nFile size: {upload_size}b")
    except:
        print("Error sending file")
        return
    return


def list_files():
    """
    List all files present on the server
    :return:
    """
    print("Requesting files...\n")
    try:
        # Send list request
        sock.send("LIST".encode('utf-8'))
    except:
        print("Couldn't make server request. Make sure a connection has bene established.")
        return
    try:
        number_of_files = struct.unpack("i", sock.recv(4))[0]
        for i in range(int(number_of_files)):
            file_name_size = struct.unpack("i", sock.recv(4))[0]
            file_name = sock.recv(file_name_size)
            print(f"\t{file_name}")
            sock.send("1".encode('utf-8'))
    except:
        print("Couldn't retrieve listing")
        return
    try:
        sock.send("1".encode('utf-8'))
        return
    except:
        print("Couldn't get final server confirmation")
        return


def download(file_name):
    """
    Download the specified file from the server
    :param file_name: name of the file that will be downloaded
    :return:
    """
    print(f"Downloading file: {file_name}")
    try:
        sock.send("DWLD".encode('utf-8'))
    except:
        print("Couldn't make server request. Make sure a connection has bene established.")
        return
    try:
        sock.recv(BUFFER_SIZE)
        sock.send(struct.pack("h", sys.getsizeof(file_name)))
        sock.send(file_name.encode('utf-8'))
        file_size = struct.unpack("i", sock.recv(4))[0]
        if file_size == -1:
            print("File does not exist. Make sure the name was entered correctly")
            return
    except:
        print("Error checking file")
    try:
        sock.send("1".encode('utf-8'))
        output_file = open(file_name, "wb")
        bytes_received = 0
        print("\nDownloading...")
        while bytes_received < file_size:
            l = sock.recv(BUFFER_SIZE)
            output_file.write(l)
            bytes_received += BUFFER_SIZE
        output_file.close()
        print(f"Successfully downloaded {file_name}")
        sock.send("1".encode('utf-8'))
        time_elapsed = struct.unpack("f", sock.recv(4))[0]
        print(f"Time elapsed: {time_elapsed}s\nFile size: {file_size}b")
    except:
        print("Error downloading file")
        return
    return


def delete(file_name):
    """
    Delete specified file from the server
    :param file_name: name of the file that will be deleted
    :return:
    """
    print(f"Deleting file: {file_name}...")
    try:
        sock.send("DELF".encode('utf-8'))
        sock.recv(BUFFER_SIZE)
    except:
        print("Couldn't connect to server. Make sure a connection has been established.")
        return
    try:
        sock.send(struct.pack("h", sys.getsizeof(file_name)))
        sock.send(file_name.encode('utf-8'))
    except:
        print("Couldn't send file details")
        return
    try:
        file_exists = struct.unpack("i", sock.recv(4))[0]
        if file_exists == -1:
            print("The file does not exist on server")
            return
    except:
        print("Couldn't determine file existence")
        return
    try:
        confirm_delete = input(f"Are you sure you want to delete {file_name}? (Y/N)\n").upper()
        while confirm_delete != "Y" and confirm_delete != "N" and confirm_delete != "YES" and confirm_delete != "NO":
            print("Command not recognised, try again")
            confirm_delete = input(f"Are you sure you want to delete {file_name}? (Y/N)\n").upper()
    except:
        print("Couldn't confirm deletion status")
        return
    try:
        if confirm_delete == "Y" or confirm_delete == "YES":
            sock.send("Y".encode('utf-8'))
            delete_status = struct.unpack("i", sock.recv(4))[0]
            if delete_status == 1:
                print("File successfully deleted")
                return
            else:
                print("File failed to delete")
                return
        else:
            sock.send("N".encode('utf-8'))
            print("Delete abandoned by user!")
            return
    except:
        print("Couldn't delete file")
        return


def quit():
    """
    Disconnect from the server
    :return:
    """
    sock.send("QUIT".encode('utf-8'))
    print("Server connection ended")
    return


print("\n\nWelcome to the FTP client."
      "\n\nCall one of the following functions:"
      "\nCONN           : Connect to server"
      "\nUPLD file_path : Upload file"
      "\nLIST           : List files"
      "\nDWLD file_path : Download file"
      "\nDELF file_path : Delete file"
      "\nQUIT           : Disconnect"
      "\nCLOS           : Close the app")

while True:
    # Listen for a command
    prompt = input("\nEnter a command: ")
    if prompt[:4].upper() == "CONN":
        connect()
    elif prompt[:4].upper() == "UPLD":
        upload(prompt[5:])
    elif prompt[:4].upper() == "LIST":
        list_files()
    elif prompt[:4].upper() == "DWLD":
        download(prompt[5:])
    elif prompt[:4].upper() == "DELF":
        delete(prompt[5:])
    elif prompt[:4].upper() == "QUIT":
        quit()
        continue
    elif prompt[:4].upper() == "CLOS":
        break
    else:
        print("Command not recognised; please try again")

sock.close()
