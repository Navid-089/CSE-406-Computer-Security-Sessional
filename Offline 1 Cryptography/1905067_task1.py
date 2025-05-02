from BitVector import * 
import importlib
bitvector_demo=importlib.import_module("1905067_bitvector_demo")
AES_helper=importlib.import_module("1905067_AES_helper")
import time
import math
import Crypto.Util.number
import threading 

def encryptionThread(chunk_iter, plaintext, IV, roundkeys):
    # Create state matrix from IV
    plainMatrix = AES_helper.createMatrix(IV)
    stateMatrix = AES_helper.createMatrix(roundkeys[0])
    stateMatrix = AES_helper.addRoundKey(stateMatrix, plainMatrix)
    
    # Perform 10 rounds of encryption
    for iteration in range(0, 10, 1):
        stateMatrix = AES_helper.encryption(stateMatrix, AES_helper.createMatrix(roundkeys[iteration+1]), iteration)
    
    # Create ciphertext by XORing with plaintext
    CipherText = AES_helper.createBitVector(stateMatrix)
    CipherText = CipherText ^ BitVector(textstring=plaintext)
    enc_output[chunk_iter] = CipherText.get_bitvector_in_ascii()

def decryptionThread(chunk_iter, ciphertext, IV, roundkeys):
    # Create state matrix from IV
    plainMatrix = AES_helper.createMatrix(IV)
    stateMatrix = AES_helper.createMatrix(roundkeys[0])
    stateMatrix = AES_helper.addRoundKey(stateMatrix, plainMatrix)
    
    # Perform 10 rounds of encryption (same as encryption in CTR mode)
    for iteration in range(0, 10, 1):
        stateMatrix = AES_helper.encryption(stateMatrix, AES_helper.createMatrix(roundkeys[iteration+1]), iteration)
    
    # Create plaintext by XORing with ciphertext
    encOut = AES_helper.createBitVector(stateMatrix)
    plaintext = encOut ^ BitVector(textstring=ciphertext)
    dec_output[chunk_iter] = plaintext.get_bitvector_in_ascii()

def main():
    # Get input key and validate
    initial_key = input("Input a 128 bit key : ")
    initial_key = AES_helper.keychecker(initial_key)
    print("Key:")
    AES_helper.initial_Print(initial_key)
    print()

    # Get plaintext
    given_plaintext = input("Input the plaintext to be sent : ")
    print("Plain Text:")
    AES_helper.initial_Print(given_plaintext)
    print()

    # Key Scheduling
    Key_ScheduingStart = time.time()
    roundkeys = []
    roundkeys.append(BitVector(textstring=initial_key))
    for i in range(0, 10, 1): 
        roundkeys.append(AES_helper.create_roundkey(roundkeys[i], AES_helper.round_constant_tuple[i]))
    Key_ScheduingEnd = time.time()

    # Encryption
    EncryptionStart = time.time()
    # Generate random IV
    A = Crypto.Util.number.getRandomNBitInteger(128)
    IV = BitVector(intVal=A, size=128)
    chunk_count = math.ceil(len(given_plaintext) / 16)

    # Initialize output lists for parallel processing
    enc_output = [""] * chunk_count
    dec_output = [""] * chunk_count

    # Encryption threads
    threads = []
    for chunk in range(0, chunk_count, 1):
        plaintext = given_plaintext[16*chunk:16*(chunk+1)]
        thread = threading.Thread(target=encryptionThread, args=(chunk, plaintext, IV, roundkeys))
        XIv = IV.intValue()
        XIv += 1
        IV = BitVector(intVal=XIv, size=128)
        threads.append(thread)

    # Start and join encryption threads
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # Combine encrypted output
    received_cipher = ""
    for x in enc_output:
        received_cipher += x

    print("Ciphered Text:")
    print(received_cipher)
    EncryptionFinish = time.time()
    print()

    # Decryption
    DecryptionStart = time.time()
    IV = BitVector(intVal=A, size=128)
    decthreads = []
    
    # Decryption threads
    for chunk in range(0, chunk_count, 1):
        ciphertext = received_cipher[16*chunk:16*(chunk+1)]
        thread = threading.Thread(target=decryptionThread, args=(chunk, ciphertext, IV, roundkeys))
        XIv = IV.intValue()
        XIv += 1
        IV = BitVector(intVal=XIv, size=128)
        decthreads.append(thread)

    # Start and join decryption threads
    for t in decthreads:
        t.start()
    for t in decthreads:
        t.join()

    # Combine decrypted output
    Deciphered_text = ""
    for x in dec_output:
        Deciphered_text += x

    print("Deciphered Text:")
    AES_helper.initial_Print(Deciphered_text, 1)
    print()
    DecryptionFinish = time.time()

    # Print timing information
    AES_helper.final_time_print(
        Key_ScheduingEnd - Key_ScheduingStart,
        EncryptionFinish - EncryptionStart,
        DecryptionFinish - DecryptionStart
    )

if __name__ == "__main__":
    main() 