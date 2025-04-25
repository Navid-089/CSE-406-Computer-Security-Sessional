import socket 
import json 
import math 
import Crypto.Util.number 
import importlib 
from BitVector import * 

aes = importlib.import_module('2005089_aes-defs') 
ecdh = importlib.import_module('2005089_ecdh_defs') 

PORT = 12345 

#ECC Setup 

a, b, G, P = ecdh.generate_curve_params(128)
priv_key_A = Crypto.Util.number.getRandomNBitInteger(128)

def start_alice(): 
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    s.connect(("localhost", PORT)) 

    print("Alice is Connected to the server.") 

    public_key_A = ecdh.ecc_scalar_mult(priv_key_A, G, a, P) 
    init_data = (a, b, G, public_key_A, P)
    s.sendall(json.dumps(init_data).encode())

    response = s.recv(2048).decode()

    public_key_B = tuple(json.loads(response))
    print("Bob's Public Key: ", public_key_B)
    shared_point = ecdh.ecc_scalar_mult(priv_key_A, public_key_B, a, P)
    shared_key = shared_point[0] 

    s.sendall("ALICE ready to transmit".encode())
    print(s.recv(1024).decode())

    print("Shared Secret Key:", shared_key)
    plaintext = input("Enter plaintext: ")
    plaintext_padded = aes.plaintext_padder(plaintext)

    aes_key_bits = bin(shared_key)[2:].zfill(128)[:128]
    round_keys = [BitVector(bitstring=aes_key_bits)]
    rcons = aes.generate_r_constant()
    for i in range(10):
        round_keys.append(aes.generate_r_key(round_keys[-1], rcons[i]))

    iv_int = Crypto.Util.number.getRandomNBitInteger(128)
    iv = BitVector(intVal=iv_int, size=128)
    iv_reset = iv.deep_copy()

    ciphertext = BitVector(size=0)
    chunks = math.ceil(len(plaintext_padded) / 16) 

    for i in range(chunks):
        block = plaintext_padded[i*16:(i+1)*16]
        block_bv = BitVector(rawbytes=block) ^ iv
        matrix = aes.create_matrix(block_bv)
        matrix = aes.xor_round_key(matrix, aes.create_matrix(round_keys[0]))

        for rnd in range(10):
            matrix = aes.encrypte(matrix, aes.create_matrix(round_keys[rnd+1]), rnd)

        enc_block = aes.create_bitvector(matrix)
        ciphertext += enc_block
        iv = enc_block

    final_packet = iv_reset + ciphertext
    s.sendall(final_packet.get_bitvector_in_ascii().encode())
    s.close()


if __name__ == "__main__":
    start_alice()

    