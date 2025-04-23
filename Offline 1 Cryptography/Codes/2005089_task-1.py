import importlib
import time 
import math
import Crypto.Util.number
from BitVector import * # type: ignore
bvd = importlib.import_module('2005089_bitvector-demo')
modulus = BitVector(bitstring='100011011') 
defs = importlib.import_module('2005089_aes-defs') 

input_key = "BUET CSE20 Batch"
#input_key = input("Enter the key: ") 
input_key = defs.key_checker(input_key) 
print("Key: ")
input_key_bv = BitVector(textstring=input_key)
defs.initial_print(input_key_bv) 
print() 

print("Plaintext: ") 
input_plaintext="We need picnic" 
input_plaintext_bv1 = BitVector(textstring=input_plaintext)
defs.initial_print(input_plaintext_bv1)
# input_plaintext = input("Input the plaintext: ") 
print("\nAfter padding: ")
input_plaintext = defs.plaintext_checker(input_plaintext)
input_plaintext_bv2 = BitVector(rawbytes=input_plaintext)
defs.initial_print(input_plaintext_bv2) 


key_start = time.time()

rcon = defs.generate_rcon()

round_keys = [BitVector(textstring=input_key)]
for i in range(10):
    next_key = defs.generate_round_key(round_keys[-1], rcon[i])
    round_keys.append(next_key)


key_end = time.time() 
key_interval = key_end - key_start

# Prepare IV and encryption setup
encrypt_start = time.time()
iv = BitVector(intVal=Crypto.Util.number.getRandomNBitInteger(128), size=128) 
init_iv = iv
ciphertext = BitVector(size=0)

# Split plaintext into 16-byte chunks
chunk_size = 16
num_chunks = math.ceil(len(input_plaintext) / chunk_size)

for i in range(num_chunks):
    # Slice the padded plaintext (raw bytes)
    chunk_bytes = input_plaintext[i * chunk_size : (i + 1) * chunk_size]
    chunk_bv = BitVector(rawbytes=chunk_bytes)

    # XOR with IV (CBC mode)
    chunk_bv ^= iv

    # Convert to state matrix
    state_matrix = defs.create_matrix(chunk_bv)

    # Initial round key addition
    state_matrix = defs.add_round_key(state_matrix, defs.create_matrix(round_keys[0]))

    # AES rounds
    for round_num in range(10):
        state_matrix = defs.encryption(state_matrix, defs.create_matrix(round_keys[round_num + 1]), round_num)

    # Flatten matrix to ciphertext block
    cipher_block = defs.create_bitvector(state_matrix)
    ciphertext += cipher_block

    # Update IV for next chunk
    iv = cipher_block 

encrypt_end = time.time()
encrypt_interval = encrypt_end - encrypt_start

print("\nCiphered Text: ") 
final_ciphertext = init_iv + ciphertext
defs.initial_print(final_ciphertext, hex_first=True) 

print("\nDeciphered Text:")

# Start timer
decrypt_start = time.time()

# Extract IV and actual ciphertext
rx_iv = final_ciphertext[:128]
rx_plaintext = final_ciphertext[128:]

# Prepare variables
decrypted_text = BitVector(size=0)
iv = rx_iv

for i in range(num_chunks):
    # Extract chunk
    cipher_chunk = rx_plaintext[i * 128 : (i + 1) * 128]

    # Convert to state matrix
    state_matrix = defs.create_matrix(cipher_chunk)

    # Final round key first
    state_matrix = defs.add_round_key(state_matrix, defs.create_matrix(round_keys[10]))

    # Inverse AES rounds
    for round_num in range(9, -1, -1):
        state_matrix = defs.decryption(state_matrix, defs.create_matrix(round_keys[round_num]), round_num)

    # Flatten and XOR with previous IV
    plain_block = defs.create_bitvector(state_matrix) ^ iv
    decrypted_text += plain_block

    # Update IV for CBC chaining
    iv = cipher_chunk

# Stop timer
decrypt_end = time.time()
decrypt_interval = decrypt_end - decrypt_start


print("Before Unpadding:")
defs.initial_print(decrypted_text, hex_first=True)


unpadded_bytes = bytes([int(decrypted_text[i:i+8]) for i in range(0, len(decrypted_text), 8)])
padding_len = unpadded_bytes[-1]
unpadded_text = unpadded_bytes[:-padding_len].decode("utf-8")

print("\nAfter Unpadding:")
defs.initial_print(BitVector(textstring=unpadded_text), hex_first=False)

print("\nExecution Time Details:")
defs.print_time(key_interval, encrypt_interval, decrypt_interval)