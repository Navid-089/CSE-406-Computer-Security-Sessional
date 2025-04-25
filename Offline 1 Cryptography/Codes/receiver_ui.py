import socket
import json
import math
import Crypto.Util.number
import importlib
from BitVector import *
import tkinter as tk
from threading import Thread

aes = importlib.import_module("2005089_aes_defs")
ecdh = importlib.import_module("2005089_ecdh_defs")

PORT = 8000

class BobGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Bob - Receiver")
        self.root.geometry("600x300")

        self.label = tk.Label(self.root, text="Received Messages:")
        self.label.pack(pady=10)

        self.display = tk.Text(self.root, width=70, height=12)
        self.display.pack(pady=5)

        thread = Thread(target=self.listen_loop)
        thread.start()

        self.root.mainloop()

    def setup_connection(self):
        self.priv_key = Crypto.Util.number.getRandomNBitInteger(128)
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind(("localhost", PORT))
        server.listen(1)
        self.client, _ = server.accept()

        a, b, G, pub_key_A, P = json.loads(self.client.recv(2048).decode())
        pub_key_B = ecdh.ecc_scalar_mult(self.priv_key, G, a, P)
        self.client.sendall(json.dumps(pub_key_B).encode())

        shared_point = ecdh.ecc_scalar_mult(self.priv_key, tuple(pub_key_A), a, P)
        self.shared_key = shared_point[0]

        self.client.recv(1024)  # ALICE ready
        self.client.sendall("BOB ready to receive".encode())

    def listen_loop(self):
        self.setup_connection()
        while True:
            try:
                data = self.client.recv(8192).decode()
                if not data:
                    break

                iv = BitVector(textstring=data[:16])
                ciphertext_text = data[16:]

                aes_key_bits = bin(self.shared_key)[2:].zfill(128)[:128]
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

                # Unpadding logic (PKCS#7)
                try:
                    last_char = plaintext[-1]
                    pad_val = ord(last_char)
                    if pad_val > 0 and pad_val <= 16 and plaintext[-pad_val:] == last_char * pad_val:
                        plaintext = plaintext[:-pad_val]
                except Exception as e:
                    print("Unpadding issue:", e)

                self.display.insert(tk.END, plaintext + "\n")


            except Exception as e:
                print("Error:", e)
                break
        self.client.close() 
        


if __name__ == "__main__":
    BobGUI()
