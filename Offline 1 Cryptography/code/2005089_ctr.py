from BitVector import * 
import importlib
import math
import Crypto.Util.number # type: ignore
import threading
import time

bitvector_demo = importlib.import_module("2005089_bitvector-demo")
defs = importlib.import_module("2005089_aes_defs")

file_input = True
file_path = "2005089_image-min.jpg"  

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

    if not file_input:
        print("\nPlain Text:")
        defs.print_inf(BitVector(rawbytes=input_bytes))

    pad_len = 16 - (len(input_bytes) % 16)
    input_bytes += bytes([pad_len] * pad_len)

    if not file_input:
        print("\nPlain Text (After padding):")
        defs.print_inf(BitVector(rawbytes=input_bytes))

    num_chunks = math.ceil(len(input_bytes) / 16)

    # === Key Expansion with timing ===
    key_start = time.time()
    rcons = defs.generate_r_constant()
    round_keys = [BitVector(textstring=input_key)]
    for i in range(10):
        round_keys.append(defs.generate_r_key(round_keys[-1], rcons[i]))
    key_end = time.time()
    key_schedule_time = key_end - key_start

    # === ENCRYPTION ===
    encrypt_start = time.time()
    randomNumber = Crypto.Util.number.getRandomNBitInteger(128)
    iv = BitVector(intVal=randomNumber, size=128)
    iv_for_increment = iv.deep_copy()

    enc_output = [None] * num_chunks
    enc_threads = []

    for i in range(num_chunks):
        block = input_bytes[i * 16:(i + 1) * 16]
        t = threading.Thread(target=encryption_thread, args=(i, block, iv_for_increment, round_keys, enc_output))
        enc_threads.append(t)
        iv_for_increment = BitVector(intVal=(iv_for_increment.intValue() + 1), size=128)

    [t.start() for t in enc_threads]
    [t.join() for t in enc_threads]

    ciphertext = BitVector(size=0)
    for chunk in enc_output:
        ciphertext += chunk

    final_ciphertext = iv + ciphertext
    encrypt_end = time.time()
    encryption_time = encrypt_end - encrypt_start

    if not file_input:
        print("\nEncrypted:")
        defs.print_inf(final_ciphertext, hex_first=True)

    # === DECRYPTION ===
    decrypt_start = time.time()
    rx_iv = final_ciphertext[:128]
    rx_ciphertext = final_ciphertext[128:]
    iv = rx_iv.deep_copy()

    dec_output = [None] * num_chunks
    dec_threads = []

    for i in range(num_chunks):
        enc_chunk = rx_ciphertext[i * 128:(i + 1) * 128]
        t = threading.Thread(target=decryption_thread, args=(i, enc_chunk, iv, round_keys, dec_output))
        dec_threads.append(t)
        iv = BitVector(intVal=(iv.intValue() + 1), size=128)

    [t.start() for t in dec_threads]
    [t.join() for t in dec_threads]

    decrypted_bv = BitVector(size=0)
    for chunk in dec_output:
        decrypted_bv += chunk

    decrypted_bytes = bytes([int(decrypted_bv[i:i+8]) for i in range(0, len(decrypted_bv), 8)])
    pad_value = decrypted_bytes[-1]
    unpadded_bytes = decrypted_bytes[:-pad_value]
    decrypt_end = time.time()
    decryption_time = decrypt_end - decrypt_start

    if file_input:
        output_path = "output_" + file_path
        with open(output_path, "wb") as f:
            f.write(unpadded_bytes)
        print(f"\n!! Decrypted file written to: {output_path}")
    else:
        print("\nDecrypted Text:")
        print(unpadded_bytes.decode('utf-8', errors='ignore'))

    # === Print timing ===
    print("\nExecution Time Details:")
    defs.print_time(key_schedule_time, encryption_time, decryption_time)

if __name__ == "__main__":
    main()
