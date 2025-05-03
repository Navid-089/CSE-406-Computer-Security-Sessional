import importlib
import time
from prettytable import PrettyTable
import Crypto.Util.number

ecc = importlib.import_module("2005089_ecdh_defs")

key_sizes = [128, 192, 256]
alice_times = [0, 0, 0]
bob_times = [0, 0, 0]
shared_times = [0, 0, 0]

print("=== Elliptic Curve Diffie-Hellman (ECDH) ===")

for i, key_bits in enumerate(key_sizes):
    print(f"\n--- Key Size: {key_bits} bits ---")
    for j in range(5): 
        print(f"--- Iteration {j + 1} ---")
        a, b, g, p = ecc.generate_curve_params(key_bits)

        # Alice's keys
        start = time.time()
        ka = Crypto.Util.number.getRandomNBitInteger(key_bits)
        # print(len(str(abs(ka))))
        alice_public = ecc.ecc_scalar_mult(ka, g, a, p)
        alice_times[i] += time.time() - start
        print("Alice's Public Key:", alice_public)

        # Bob's keys
        start = time.time()
        kb = Crypto.Util.number.getRandomNBitInteger(key_bits)
        bob_public = ecc.ecc_scalar_mult(kb, g, a, p)
        bob_times[i] += time.time() - start
        print("\nBob's Public Key:", bob_public)

        # Shared key
        start = time.time()
        shared_by_alice = ecc.ecc_scalar_mult(ka, bob_public, a, p)
        shared_by_bob = ecc.ecc_scalar_mult(kb, alice_public, a, p)
        shared_times[i] += time.time() - start

        print("\nShared Key (Alice):", shared_by_alice)
        print("Shared Key (Bob):  ", shared_by_bob) 
        print("\n\n")

# Display timing results
table = PrettyTable()
table.field_names = ["Key Size (bits)", "Alice (ms)", "Bob (ms)", "Shared Key R (ms)"]

for i in range(3):
    table.add_row([
        key_sizes[i],
        round(alice_times[i] * 1000 / 5, 4),
        round(bob_times[i] * 1000 / 5, 4),
        round(shared_times[i] * 1000 / 5, 4)
    ])

print("\n=== Timing Results ===")
print(table)