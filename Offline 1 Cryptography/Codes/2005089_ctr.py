from BitVector import * 
import importlib
import math
import Crypto.Util.number
import threading

bitvector_demo = importlib.import_module("2005089_bitvector-demo")
defs = importlib.import_module("2005089_aes_defs")

file_input = True
file_path = "image-min.jpg"  # Change to your target file

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
    input_key = "BUET CSE20 Batch"
    input_key = defs.key_length_checker(input_key)
    print("Key:")
    defs.print_inf(BitVector(textstring=input_key))

    if file_input:
        with open(file_path, "rb") as f:
            input_bytes = f.read()
    else:
        input_bytes = b"We need picnicccWe need picniccc"

    pad_len = 16 - (len(input_bytes) % 16)
    input_bytes += bytes([pad_len] * pad_len)

    if not file_input:
        print("\nPlain Text:")
        defs.print_inf(BitVector(rawbytes=input_bytes))

    num_chunks = math.ceil(len(input_bytes) / 16)

    # Key Expansion
    rcons = defs.generate_r_constant()
    round_keys = [BitVector(textstring=input_key)]
    for i in range(10):
        round_keys.append(defs.generate_r_key(round_keys[-1], rcons[i]))

    # Encryption
    A = Crypto.Util.number.getRandomNBitInteger(128)
    A = 232833907129507839396865044293246588104
    IV = BitVector(intVal=A, size=128)
    enc_output = [None] * num_chunks
    enc_threads = []

    for i in range(num_chunks):
        block = input_bytes[i*16:(i+1)*16]
        t = threading.Thread(target=encryption_thread, args=(i, block, IV, round_keys, enc_output))
        enc_threads.append(t)
        IV = BitVector(intVal=(IV.intValue() + 1), size=128)

    for t in enc_threads: t.start()
    for t in enc_threads: t.join()

    ciphertext = BitVector(size=0)
    for chunk in enc_output:
        ciphertext += chunk

    if not file_input:
        print("\nEncrypted (hex):")
        defs.print_inf(ciphertext, hex_first=True)

    # Decryption
    IV = BitVector(intVal=A, size=128)
    dec_output = [None] * num_chunks
    dec_threads = []

    for i in range(num_chunks):
        enc_chunk = enc_output[i]
        t = threading.Thread(target=decryption_thread, args=(i, enc_chunk, IV, round_keys, dec_output))
        dec_threads.append(t)
        IV = BitVector(intVal=(IV.intValue() + 1), size=128)

    for t in dec_threads: t.start()
    for t in dec_threads: t.join()

    decrypted_bv = BitVector(size=0)
    for chunk in dec_output:
        decrypted_bv += chunk

    decrypted_bytes = bytes([int(decrypted_bv[i:i+8]) for i in range(0, len(decrypted_bv), 8)])
    pad_value = decrypted_bytes[-1]
    unpadded_bytes = decrypted_bytes[:-pad_value]

    if file_input:
        output_path = "output_" + file_path
        with open(output_path, "wb") as f:
            f.write(unpadded_bytes)
        print(f"\n!! Decrypted file written to: {output_path}")
    else:
        print("\nDecrypted Text:")
        print(unpadded_bytes.decode('utf-8', errors='ignore'))

if __name__ == "__main__":
    main()
