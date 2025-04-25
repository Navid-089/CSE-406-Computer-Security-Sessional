# 2005089_task3_sender_gui.py

import socket
import json
import math
import Crypto.Util.number
import importlib
from BitVector import *
import tkinter as tk
from tkinter import messagebox, simpledialog
from threading import Thread

aes = importlib.import_module("2005089_aes-defs")
ecdh = importlib.import_module("2005089_ecdh_defs")

PORT = 8000

class AliceGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Alice - Sender")
        self.root.geometry("500x350")

        self.label = tk.Label(self.root, text="Enter Message:")
        self.label.pack(pady=10)

        self.text_entry = tk.Entry(self.root, width=60)
        self.text_entry.pack(pady=5)

        self.send_button = tk.Button(self.root, text="Send Secure Message", command=self.send_message)
        self.send_button.pack(pady=15)

        self.status = tk.Label(self.root, text="", fg="green")
        self.status.pack(pady=10)

        self.setup_ecdh()

        self.root.mainloop()

    def setup_ecdh(self):
        self.a, self.b, self.G, self.P = ecdh.generate_curve_params(128)
        self.priv_key = Crypto.Util.number.getRandomNBitInteger(128)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(("localhost", PORT))

        pub_key = ecdh.ecc_scalar_mult(self.priv_key, self.G, self.a, self.P)
        self.sock.sendall(json.dumps((self.a, self.b, self.G, pub_key, self.P)).encode())

        bob_pub = json.loads(self.sock.recv(2048).decode())
        self.shared_point = ecdh.ecc_scalar_mult(self.priv_key, tuple(bob_pub), self.a, self.P)
        self.shared_key = self.shared_point[0]

        self.sock.sendall("ALICE ready to transmit".encode())
        self.sock.recv(1024)  # Wait for BOB

    def send_message(self):
        plaintext = self.text_entry.get()
        if not plaintext:
            messagebox.showerror("Error", "Message cannot be empty")
            return

        padded = aes.plaintext_padder(plaintext)
        aes_key_bits = bin(self.shared_key)[2:].zfill(128)[:128]
        round_keys = [BitVector(bitstring=aes_key_bits)]
        rcons = aes.generate_r_constant()
        for i in range(10):
            round_keys.append(aes.generate_r_key(round_keys[-1], rcons[i]))

        iv_int = Crypto.Util.number.getRandomNBitInteger(128)
        iv = BitVector(intVal=iv_int, size=128)
        iv_reset = iv.deep_copy()

        ciphertext = BitVector(size=0)
        chunks = math.ceil(len(padded) / 16)

        for i in range(chunks):
            block = padded[i*16:(i+1)*16]
            block_bv = BitVector(rawbytes=block) ^ iv
            matrix = aes.create_matrix(block_bv)
            matrix = aes.xor_round_key(matrix, aes.create_matrix(round_keys[0]))

            for rnd in range(10):
                matrix = aes.encrypte(matrix, aes.create_matrix(round_keys[rnd+1]), rnd)

            enc_block = aes.create_bitvector(matrix)
            ciphertext += enc_block
            iv = enc_block

        final_packet = iv_reset + ciphertext
        self.sock.sendall(final_packet.get_bitvector_in_ascii().encode())
        self.status.config(text="Message sent securely!")
        self.text_entry.delete(0, tk.END)


if __name__ == "__main__":
    AliceGUI()