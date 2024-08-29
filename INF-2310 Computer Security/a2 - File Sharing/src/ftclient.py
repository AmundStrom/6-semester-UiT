# Sources:
# Socket logic: https://pythonprogramming.net/pickle-objects-sockets-tutorial-python-3/
# RSA logic: https://pycryptodome.readthedocs.io/en/latest/src/public_key/rsa.html
# AES logic: aes-intro.py

import socket
import pickle
import sys

from Crypto.Cipher import AES as aes
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

from Crypto.PublicKey import RSA as rsa
from Crypto.Cipher import PKCS1_OAEP


HEADERSIZE = 10
RECV_SIZE = 16


def receive_file(hostname, tcp_port, save_path):
    """
    Will receive a file and store it.
    Recieves the file from the given port and store it at the given path.
    """

    # Now the server knows about us
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((hostname, tcp_port))

    full_msg = b""

    # Step 1: Server task

    ### Step 2: RECV -> Server Public key ###
    full_msg = recv_data(s)
    full_msg = full_msg.decode('utf-8')
    public_key = rsa.import_key(full_msg)

    ### Step 3: SEND -> Encrypted Symmetric key ###
    symmetric_key = get_random_bytes(32)

    # Encrypt the Symmetric key using the given Public key
    rsa_cipher = PKCS1_OAEP.new(public_key)
    encrypted_symmetric_key = rsa_cipher.encrypt(symmetric_key)

    # Send encrypted Symmetric key
    data = pickle.dumps(encrypted_symmetric_key)
    send_data(s, data)

    # Step 4: Server task
    # Step 5: Server task

    ### Step 6: RECV -> Encrypted file ###
    with open(save_path, 'wb') as f:

        # Receive the encrypted file and initialization vector (iv)
        full_msg = recv_data(s)
        full_msg = pickle.loads(full_msg)
        iv = full_msg[:aes.block_size]
        encrypted_file = full_msg[aes.block_size:]

        # Decrypt the file using the symmetric key and initialization vector
        aes_decipher = aes.new(symmetric_key, aes.MODE_CBC, iv=iv)
        file = aes_decipher.decrypt(encrypted_file)
        file = unpad(file, aes.block_size)

        f.write(file)

    print("File received successfully")


def send_data(socket : socket.socket, data : bytes):
    """
    Helper function to send data.
    """

    # Create a "Header" at the start of the message to tell the receiver how large the message is in bytes
    msg = bytes(f"{len(data):<{HEADERSIZE}}", 'utf-8') + data
    
    # Send message
    print(f"Data sent from client: \n{msg}\n")
    socket.send(msg)


def recv_data(socket : socket.socket) -> bytes:
    """
    Helper function to recieve data
    """

    full_msg = b""
    new_msg = True

    while True:
        # Receive data in upredictable bytes at a time
        data = socket.recv(RECV_SIZE)

        # Check if this is the first received data
        if new_msg:
            # Read header to find the size of the entire message in bytes
            msg_len = int(data[:HEADERSIZE])
            new_msg = False

        full_msg += data

        # Check if recieved full message
        if len(full_msg) - HEADERSIZE == msg_len:
            print(f"Data received in client: \n{full_msg}\n")
            return full_msg[HEADERSIZE:]


def main():
    # Check if the correct number of arguments is provided
    if len(sys.argv) != 2:
        print("Usage: python ftclient.py <hostname of the server>")
        return

    arg = sys.argv[1]

    receive_file(arg, 12345, "receivedData.txt")


if __name__ == "__main__":
    main()
