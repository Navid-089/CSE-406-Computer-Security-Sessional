import socket
import json
import math
import Crypto.Util.number #type: ignore
import importlib
import os
from BitVector import *

aes = importlib.import_module("2005089_aes_defs")
ecdh = importlib.import_module('2005089_ecdh_defs')

PORT = 12345
file_input = True
file_path = "2005089_image-min.jpg"

# ECC Setup
a, b, G, P = ecdh.generate_curve_params(128)
priv_key_A = Crypto.Util.number.getRandomNBitInteger(128)

def start_alice():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    s.connect(("localhost", PORT)) 

    # ECC Key Exchange
    public_key_A = ecdh.ecc_scalar_mult(priv_key_A, G, a, P) 
    init_data = (a, b, G, public_key_A, P)
    s.sendall(json.dumps(init_data).encode())

    response = s.recv(2048).decode()
    public_key_B = tuple(json.loads(response))
    shared_point = ecdh.ecc_scalar_mult(priv_key_A, public_key_B, a, P)
    shared_key = shared_point[0] 

    # Prepare AES key
    aes_key_bits = bin(shared_key)[2:].zfill(128)[:128]
    round_keys = [BitVector(bitstring=aes_key_bits)]
    rcons = aes.generate_r_constant()
    for i in range(10):
        round_keys.append(aes.generate_r_key(round_keys[-1], rcons[i]))

    # === ENCRYPT FILENAME ===
    filename = os.path.basename(file_path).encode()
    pad_len = 16 - (len(filename) % 16)
    filename += bytes([pad_len] * pad_len)

    iv_name = BitVector(intVal=Crypto.Util.number.getRandomNBitInteger(128), size=128)
    iv_reset_name = iv_name.deep_copy()

    cipher_name = BitVector(size=0)
    for i in range(0, len(filename), 16):
        block = filename[i:i+16]
        bv_block = BitVector(rawbytes=block) ^ iv_name
        state = aes.create_matrix(bv_block)
        state = aes.xor_round_key(state, aes.create_matrix(round_keys[0]))
        for rnd in range(10):
            state = aes.encrypte(state, aes.create_matrix(round_keys[rnd + 1]), rnd)
        out_block = aes.create_bitvector(state)
        cipher_name += out_block
        iv_name = out_block

    # Send IV + Encrypted filename
    s.sendall((iv_reset_name + cipher_name).get_bitvector_in_ascii().encode())
    s.recv(1024)  # ACK

    s.sendall("ALICE ready to transmit".encode())
    s.recv(1024)  # "BOB ready"

    # === Encrypt File Content ===
    if not file_input:
        print("Type 'kill' to exit")
    while True:
        if file_input:
            with open(file_path, "rb") as f:
                input_bytes = f.read()
        else:
            
            input_text = input("Enter plaintext: ")
            if(input_text == "kill"):
                break

            input_bytes = input_text.encode('utf-8')
        if not file_input:
            aes.print_inf(BitVector(textstring = input_text))
        else:
            print("Encrypting file ...")
        pad_len = 16 - (len(input_bytes) % 16)
        input_bytes += bytes([pad_len] * pad_len)
        if not file_input:
            print("After Padding:")
            aes.print_inf(BitVector(rawbytes=input_bytes))

        iv_int = Crypto.Util.number.getRandomNBitInteger(128)
        iv = BitVector(intVal=iv_int, size=128)
        iv_reset = iv.deep_copy()

        ciphertext = BitVector(size=0)
        chunks = math.ceil(len(input_bytes) / 16) 

        for i in range(chunks):
            block = input_bytes[i*16:(i+1)*16]
            bv_block = BitVector(rawbytes=block) ^ iv
            state = aes.create_matrix(bv_block)
            state = aes.xor_round_key(state, aes.create_matrix(round_keys[0]))
            for rnd in range(10):
                state = aes.encrypte(state, aes.create_matrix(round_keys[rnd+1]), rnd)
            out_block = aes.create_bitvector(state)
            ciphertext += out_block
            iv = out_block

        final_packet = iv_reset + ciphertext 
        if not file_input:
            print("Ciphertext:")
            aes.print_inf(final_packet, hex_first=True)
        else:
            print("Encrypted file content and sent!")

        s.sendall(final_packet.get_bitvector_in_ascii().encode())
        if(file_input): 
            break;
    s.close()   

if __name__ == "__main__":
    start_alice() 