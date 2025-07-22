import importlib
import time 
import math
import Crypto.Util.number # type: ignore
from BitVector import *  # type: ignore


bvd = importlib.import_module('2005089_bitvector-demo')
defs = importlib.import_module('2005089_aes_defs')
modulus = BitVector(bitstring='100011011') 

# File mode
file_input = False
file_path = "2005089_image-min.jpg"  # Your file name here

# Key setup
input_key = "BUET CSE20 Batch"
input_key = defs.key_length_checker(input_key)
input_key_bv = BitVector(textstring=input_key)
print("Key:")
defs.print_inf(input_key_bv)

# Read data
if file_input:
    with open(file_path, "rb") as f:
        input_bytes = f.read()
else:
    # input_text = input("Enter plaintext: ")
    # input_bytes = input_text.encode('utf-8')
    input_bytes = b"We need picnicc"

# Padding   
input_bytes_bv = BitVector(rawbytes=input_bytes) 
if not file_input:
    print("\nPlain Text:") 
    defs.print_inf(input_bytes_bv)

pad_len = 16 - (len(input_bytes) % 16)
input_bytes += bytes([pad_len] * pad_len) 

input_plaintext_bv = BitVector(rawbytes=input_bytes)

if not file_input:
    print("\nAfter Padding:")
    defs.print_inf(input_plaintext_bv)

# Key Expansion
key_start = time.time()
rcon = defs.generate_r_constant()
round_keys = [BitVector(textstring=input_key)]
for i in range(10):
    round_keys.append(defs.generate_r_key(round_keys[-1], rcon[i]))
key_end = time.time()
key_interval = key_end - key_start

# Encryption
encrypt_start = time.time()
iv = BitVector(intVal=Crypto.Util.number.getRandomNBitInteger(128), size=128) 
init_iv = iv.deep_copy()
ciphertext = BitVector(size=0)

chunk_size = 16
num_chunks = math.ceil(len(input_bytes) / chunk_size)

for i in range(num_chunks):
    chunk = input_bytes[i * chunk_size : (i + 1) * chunk_size]
    chunk_bv = BitVector(rawbytes=chunk) ^ iv

    state = defs.create_matrix(chunk_bv)
    state = defs.xor_round_key(state, defs.create_matrix(round_keys[0]))
    for rnd in range(10):
        state = defs.encrypte(state, defs.create_matrix(round_keys[rnd + 1]), rnd)

    cipher_block = defs.create_bitvector(state)
    ciphertext += cipher_block
    iv = cipher_block

encrypt_end = time.time()
encrypt_interval = encrypt_end - encrypt_start

final_ciphertext = init_iv + ciphertext

if not file_input:
    print("\nCiphered Text:")
    defs.print_inf(final_ciphertext, hex_first=True)

# Decryption
decrypt_start = time.time()
rx_iv = final_ciphertext[:128]
rx_plaintext = final_ciphertext[128:]
iv = rx_iv
decrypted_bv = BitVector(size=0)

for i in range(num_chunks):
    cipher_chunk = rx_plaintext[i * 128 : (i + 1) * 128]
    state = defs.create_matrix(cipher_chunk)
    state = defs.xor_round_key(state, defs.create_matrix(round_keys[10]))
    for rnd in range(9, -1, -1):
        state = defs.decrypte(state, defs.create_matrix(round_keys[rnd]), rnd)
    plain_block = defs.create_bitvector(state) ^ iv
    decrypted_bv += plain_block
    iv = cipher_chunk

decrypt_end = time.time()
decrypt_interval = decrypt_end - decrypt_start

# Unpadding
if not file_input:
    print("\nBefore Unpadding:") 
    defs.print_inf(decrypted_bv, hex_first=True)

decrypted_bytes = bytes([int(decrypted_bv[i:i+8]) for i in range(0, len(decrypted_bv), 8)])

pad_value = decrypted_bytes[-1]
unpadded_bytes = decrypted_bytes[:-pad_value]

if file_input:
    output_path = "output_" + file_path
    with open(output_path, "wb") as f:
        f.write(unpadded_bytes)
    print(f"\n!! Decrypted file written to: {output_path}")
else:
    print("\nAfter Unpadding:")
    defs.print_inf(BitVector(rawbytes=unpadded_bytes), hex_first=False)

# Timing
print("\nExecution Time Details:")
defs.print_time(key_interval, encrypt_interval, decrypt_interval)