import socket
import json
import math
import Crypto.Util.number
import importlib
from BitVector import *

aes = importlib.import_module("2005089_aes_defs")
ecdh = importlib.import_module("2005089_ecdh_defs")

PORT = 12345
priv_key_B = Crypto.Util.number.getRandomNBitInteger(128)


def start_bob():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("localhost", PORT))
    server.listen(1)

    client, tmp = server.accept()

    received = json.loads(client.recv(2048).decode())
    a, b, G, public_key_A, P = received

    public_key_B = ecdh.ecc_scalar_mult(priv_key_B, G, a, P)
    client.sendall(json.dumps(public_key_B).encode())

    shared_point = ecdh.ecc_scalar_mult(priv_key_B, tuple(public_key_A), a, P)
    shared_key = shared_point[0]

    print(client.recv(1024).decode())
    client.sendall("BOB ready to receive".encode())

    print("Shared Secret Key:", shared_key)

    data = client.recv(8192).decode()
    iv_text = data[:16]
    iv = BitVector(textstring=iv_text)
    ciphertext_text = data[16:]

    aes_key_bits = bin(shared_key)[2:].zfill(128)[:128]
    round_keys = [BitVector(bitstring=aes_key_bits)]
    rcons = aes.generate_r_constant()
    for i in range(10):
        round_keys.append(aes.generate_r_key(round_keys[-1], rcons[i]))

    plaintext = ""
    chunks = math.ceil(len(ciphertext_text) / 16)
    for i in range(chunks):
        block = ciphertext_text[i*16:(i+1)*16]
        block_bv = BitVector(textstring=block)
        matrix = aes.create_matrix(block_bv)
        matrix = aes.xor_round_key(matrix, aes.create_matrix(round_keys[10]))

        for rnd in reversed(range(10)):
            matrix = aes.decrypte(matrix, aes.create_matrix(round_keys[rnd]), rnd)

        decrypted_bv = aes.create_bitvector(matrix) ^ iv
        iv = block_bv
        plaintext += decrypted_bv.get_bitvector_in_ascii()

    # PKCS#7 Unpadding
    try:
        pad_byte = ord(plaintext[-1])
        if 0 < pad_byte <= 16 and plaintext[-pad_byte:] == chr(pad_byte) * pad_byte:
            plaintext = plaintext[:-pad_byte]
    except Exception as e:
        print("Unpadding error:", e)

    print("Decrypted Text:", plaintext)

    client.close()
    server.close()


if __name__ == "__main__":
    start_bob()
