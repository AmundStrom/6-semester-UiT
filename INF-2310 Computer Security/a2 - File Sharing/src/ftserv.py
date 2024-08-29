# Sources:
# Socket logic: https://pythonprogramming.net/pickle-objects-sockets-tutorial-python-3/
# RSA logic: https://pycryptodome.readthedocs.io/en/latest/src/public_key/rsa.html
# AES logic: aes-intro.py


import socket
import pickle
import sys
import os

from Crypto.Cipher import AES as aes
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad, unpad

from Crypto.PublicKey import RSA as rsa
from Crypto.Cipher import PKCS1_OAEP


HEADERSIZE = 10
RECV_SIZE = 16


def generate_keys():
    """
    Will generate a private and public key pair.
    It will either import existing keys in the directory,
    or generate a new key pair and create a "pem" file for each key.
    """

    private_key, public_key = None, None

    if os.path.exists("./privatekey.pem") and os.path.exists("./publickey.pem"):
        # If Private and Public key already exists
        print("Importing existing keys")

        # Import keys
        with open("privatekey.pem", "rb") as f:
            data = f.read()
            private_key = rsa.import_key(data)

        with open("publickey.pem", "rb") as f:
            data = f.read()
            public_key = rsa.import_key(data)

    else:
        # If Private and Public key does not exists
        print("Generating new keys")

        # Generate new keys
        keys = rsa.generate(3072)

        # Export keys
        private_key = keys
        with open("privatekey.pem", "wb") as f:
            data = keys.export_key()
            f.write(data)

        public_key = keys.public_key()
        with open("publickey.pem", "wb") as f:
            data = keys.public_key().export_key()
            f.write(data)

    return private_key, public_key


def send_file(tcp_port, file_path):
    """
    Will send a file.
    Listens on the given TCP port,
    and sends the given file when a connection is established.
    """

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((socket.gethostname(), tcp_port))
    s.listen(5)

    private_key, public_key = generate_keys()

    print(f"Server has hostname {socket.gethostname()}")
    print(f"Server listening on port {tcp_port}")

    while True:
        # now our endpoint knows about the OTHER endpoint.
        client_socket, address = s.accept()
        print(f"Connection from {address} has been established.")

        full_msg = b""

        ### Step 1: SEND -> Server's Public key ###
        data = public_key.export_key()
        send_data(client_socket, data)

        # Step 2: Client task
        # Step 3: Client task

        ### Step 4: RECV -> Encrypted Symmetric key ###
        full_msg = recv_data(client_socket)
        encrypted_symmetric_key = pickle.loads(full_msg)

        # Decrypt the Symmetric key using the private key
        rsa_decipher = PKCS1_OAEP.new(private_key)
        symmetric_key = rsa_decipher.decrypt(encrypted_symmetric_key)

        ### Step 5: SEND -> Encrypted file using the Symmetric key ###
        # Open file and treat it as a binary file
        with open(file_path, 'rb') as f:
            
            file = f.read()

            # Encrypt the file
            # Generate the initialization vector (iv) used during the encryption and decryption process
            iv = get_random_bytes(aes.block_size) 
            aes_cipher = aes.new(symmetric_key, aes.MODE_CBC, iv=iv)
            ciphertext = aes_cipher.encrypt(pad(file, aes.block_size))
        
            # Send the initialization vector and cipher text
            data = pickle.dumps(iv + ciphertext)
            send_data(client_socket, data)

        print("File sent successfully")


def send_data(socket : socket.socket, data : bytes):
    """
    Helper function to send data.
    """

    # Create a "Header" at the start of the message to tell the receiver how large the message is in bytes
    msg = bytes(f"{len(data):<{HEADERSIZE}}", 'utf-8') + data
    
    print(f"Data sent from serever: \n{msg}\n")
    # Send message
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
            print(f"Data received in server: \n{full_msg}\n")
            return full_msg[HEADERSIZE:]


def main():
    # Check if the correct number of arguments is provided
    if len(sys.argv) != 2:
        print("Usage: python ftserv.py <path/to/file>")
        return

    arg = sys.argv[1]

    send_file(12345, arg)


if __name__ == "__main__":
    main()
