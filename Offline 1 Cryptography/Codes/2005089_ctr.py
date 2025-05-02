from BitVector import * 
import importlib
import math
import Crypto.Util.number
import threading

# === Helpers
bitvector_demo = importlib.import_module("2005089_bitvector-demo")
defs = importlib.import_module("2005089_aes_defs")

def encryption_thread(chunk_idx, block, iv, round_keys, output):
    counter_bv = iv.deep_copy()
    counter_state = defs.create_matrix(counter_bv)
    counter_state = defs.xor_round_key(counter_state, defs.create_matrix(round_keys[0]))
    for rnd in range(10):
        counter_state = defs.encrypte(counter_state, defs.create_matrix(round_keys[rnd + 1]), rnd)
    keystream = defs.create_bitvector(counter_state)
    output[chunk_idx] = keystream ^ BitVector(rawbytes=block)

def decryption_thread(chunk_idx, enc_chunk, iv, round_keys, output):
    counter_bv = iv.deep_copy()
    counter_state = defs.create_matrix(counter_bv)
    counter_state = defs.xor_round_key(counter_state, defs.create_matrix(round_keys[0]))
    for rnd in range(10):
        counter_state = defs.encrypte(counter_state, defs.create_matrix(round_keys[rnd + 1]), rnd)
    keystream = defs.create_bitvector(counter_state)
    output[chunk_idx] = keystream ^ enc_chunk

def main():
    file_input = False
    given_plaintext = b"We need picnicccWe need picniccc"
    input_key = "BUET CSE20 Batch"
    input_key = defs.key_length_checker(input_key)
    
    print("Key:")
    defs.print_inf(BitVector(textstring=input_key))

    pad_len = 16 - (len(given_plaintext) % 16)
    given_plaintext += bytes([pad_len] * pad_len)
    defs.print_inf(BitVector(rawbytes=given_plaintext))
    num_chunks = math.ceil(len(given_plaintext) / 16)

    # Key Expansion
    round_keys = [BitVector(textstring=input_key)]
    rcons = defs.generate_r_constant()
    for i in range(10):
        round_keys.append(defs.generate_r_key(round_keys[-1], rcons[i]))

    # Encryption
    A = Crypto.Util.number.getRandomNBitInteger(128)
    A = 232833907129507839396865044293246588104
    IV = BitVector(intVal=A, size=128)
    enc_output = [None] * num_chunks
    threads = []

    for i in range(num_chunks):
        block = given_plaintext[i*16:(i+1)*16]
        thread = threading.Thread(target=encryption_thread, args=(i, block, IV, round_keys, enc_output))
        threads.append(thread)
        IV = BitVector(intVal=(IV.intValue() + 1), size=128)

    [t.start() for t in threads]
    [t.join() for t in threads]
    
    ciphertext = BitVector(size=0)
    for chunk in enc_output:
        ciphertext += chunk

    print("\nEncrypted (hex):")
    defs.print_inf(ciphertext, hex_first=True)

    # Decryption
    IV = BitVector(intVal=A, size=128)
    dec_output = [None] * num_chunks
    dec_threads = []

    for i in range(num_chunks):
        enc_chunk = enc_output[i]
        thread = threading.Thread(target=decryption_thread, args=(i, enc_chunk, IV, round_keys, dec_output))
        dec_threads.append(thread)
        IV = BitVector(intVal=(IV.intValue() + 1), size=128)

    [t.start() for t in dec_threads]
    [t.join() for t in dec_threads]

    decrypted_bv = BitVector(size=0)
    for chunk in dec_output:
        decrypted_bv += chunk

    decrypted_bytes = bytes([int(decrypted_bv[i:i+8]) for i in range(0, len(decrypted_bv), 8)])
    pad_val = decrypted_bytes[-1]
    plain_bytes = decrypted_bytes[:-pad_val]

    print("\nDecrypted Plaintext:")
    print(plain_bytes.decode('utf-8', errors='ignore'))

if __name__ == "__main__":
    main()
