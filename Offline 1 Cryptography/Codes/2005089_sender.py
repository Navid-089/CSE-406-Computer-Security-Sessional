import socket
import json
import math
import Crypto.Util.number
import importlib
from BitVector import *

aes = importlib.import_module("2005089_aes_defs")
ecdh = importlib.import_module('2005089_ecdh_defs')

PORT = 12345
file_input = True
file_path = "image-min.jpg"

# ECC Setup
a, b, G, P = ecdh.generate_curve_params(128)
priv_key_A = Crypto.Util.number.getRandomNBitInteger(128)

def start_alice(): 
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    s.connect(("localhost", PORT)) 
    print("Alice is Connected to the server.") 

    s.sendall(file_path.encode())  # e.g., "screenshot.jpg"
    ack = s.recv(1024)  

    public_key_A = ecdh.ecc_scalar_mult(priv_key_A, G, a, P) 
    init_data = (a, b, G, public_key_A, P)
    s.sendall(json.dumps(init_data).encode())

    response = s.recv(2048).decode()
    public_key_B = tuple(json.loads(response))
    shared_point = ecdh.ecc_scalar_mult(priv_key_A, public_key_B, a, P)
    shared_key = shared_point[0] 

    s.sendall("ALICE ready to transmit".encode())
    s.recv(1024)

    print("Shared Secret Key:", shared_key)

    if file_input:
        with open(file_path, "rb") as f:
            input_bytes = f.read()
    else:
        input_text = input("Enter plaintext: ")
        input_bytes = input_text.encode('utf-8')

    pad_len = 16 - (len(input_bytes) % 16)
    input_bytes += bytes([pad_len] * pad_len)

    print("Encrypting ... ")

    aes_key_bits = bin(shared_key)[2:].zfill(128)[:128]
    round_keys = [BitVector(bitstring=aes_key_bits)]
    rcons = aes.generate_r_constant()
    for i in range(10):
        round_keys.append(aes.generate_r_key(round_keys[-1], rcons[i]))

    iv_int = Crypto.Util.number.getRandomNBitInteger(128)
    iv = BitVector(intVal=iv_int, size=128)
    iv_reset = iv.deep_copy()

    ciphertext = BitVector(size=0)
    chunks = math.ceil(len(input_bytes) / 16) 

    for i in range(chunks):
        block = input_bytes[i*16:(i+1)*16]
        block_bv = BitVector(rawbytes=block) ^ iv
        matrix = aes.create_matrix(block_bv)
        matrix = aes.xor_round_key(matrix, aes.create_matrix(round_keys[0]))

        for rnd in range(10):
            matrix = aes.encrypte(matrix, aes.create_matrix(round_keys[rnd+1]), rnd)

        enc_block = aes.create_bitvector(matrix)
        ciphertext += enc_block
        iv = enc_block

    final_packet = iv_reset + ciphertext
    print("Encryption Done! Sending data ...")
    s.sendall(final_packet.get_bitvector_in_ascii().encode())
    s.close()

if __name__ == "__main__":
    start_alice()