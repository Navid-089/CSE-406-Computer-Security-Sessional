import random, string
import importlib
from BitVector import BitVector # type: ignore
bvd = importlib.import_module('2005089_bitvector-demo')
modulus = BitVector(bitstring='100011011')  # x^7 + x^4 + x^3 + x + 1

def generate_r_constant():
    rcon = []
    rc = 0x01
    for i in range(10):
        # Append as 32-bit word (rc || 00 || 00 || 00)
        rcon.append(BitVector(intVal=rc, size=8) + BitVector(size=24))
        rc <<= 1
        if rc & 0x100:  # If it overflows 8 bits
            rc ^= 0x11B
        rc &= 0xFF  # Trim to 8 bits
    return rcon 

def g_mult(word, rc):
    shifted = word << 8
    substituted = substitute_bitvector(shifted)
    return substituted ^ rc

def generate_r_key(prev_key, rcon):
    w0 = prev_key[0:32]
    w1 = prev_key[32:64]
    w2 = prev_key[64:96]
    w3 = prev_key[96:128]

    g = g_mult(w3, rcon)

    w4 = w0 ^ g
    w5 = w4 ^ w1
    w6 = w5 ^ w2
    w7 = w6 ^ w3

    return w4 + w5 + w6 + w7 

def random_padding_generator(length):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def key_length_checker(key):
    if len(key) < 16:
        key += random_padding_generator(16 - len(key))
    else:
        key = key[:16]
    return key

def plaintext_padder(plaintext):
    byte_data = plaintext.encode('utf-8')
    pad_len = 16 - (len(byte_data) % 16) 
    return byte_data + bytes([pad_len] * pad_len)

def print_time(kst,et,dt):
    print("Key Schedule Time: ", kst * 1000, " ms")
    print("Encryption Time: ", et * 1000, " ms")
    print("Decryption Time: ", dt * 1000, " ms")

def print_ascii(str):
    try:
        print(str.get_bitvector_in_ascii())
    except:
        print("Non-printable ASCII")

def print_hex(str):
    try:
        hex_str = str.get_bitvector_in_hex()
    except: 
        print("Function not available")
    hex_formatted = " ".join(hex_str[i:i+2] for i in range(0, len(hex_str), 2))
    print(hex_formatted)

def print_inf(bv, hex_first: bool = False):
    if hex_first:
        print("In Hex:", end=" ")
        print_hex(bv)
        print("In ASCII:", end=" ")
        print_ascii(bv)
    else:
        print("In ASCII:", end=" ")
        print_ascii(bv)
        print("In Hex:", end=" ")
        print_hex(bv)

def create_matrix(bv):
    matrix = []
    for i in range(4):  # rows
        row = []
        for j in range(4):  # columns
            byte = bv[8 * (4 * j + i) : 8 * (4 * j + i + 1)]
            row.append(byte)
        matrix.append(row)
    return matrix

def create_bitvector(matrix): 
    result = BitVector(size=0)
    for i in range(4):
        for j in range(4):
            result += matrix[j][i]
    return result

def print_matrix(matrix):
    for i in range(4):
        for j in range(4):
            print_hex(matrix[i][j]) 
        print()

def substitute_bitvector(matrix): 
    result = BitVector(size=0)
    for i in range(0, matrix.length(),8):
        byte = matrix[i:i+8] 
        sub_val = bvd.Sbox[byte.intValue()]
        result+= BitVector(intVal=sub_val, size=8)
    return result 

def substitute_matrix_bytes(matrix):
    result = []
    for row in matrix:
        new_row = [BitVector(intVal=bvd.Sbox[cell.intValue()], size=8) for cell in row]
        result.append(new_row)
    return result

def inverse_substitute_matrix_bytes(matrix):
    result = []
    for row in matrix:
        new_row = [BitVector(intVal=bvd.InvSbox[cell.intValue()], size=8) for cell in row]
        result.append(new_row)
    return result


def xor_round_key(matrix, key_matrix):
    return [
        [matrix[i][j] ^ key_matrix[i][j] for j in range(4)]
        for i in range(4)
    ]

def shift_rows(matrix):
    result = []
    for i in range(4):
        row = BitVector(size=0)
        for cell in matrix[i]:
            row += cell
        shifted = row << (8 * i)
        result.append([shifted[8 * j:8 * (j + 1)] for j in range(4)])
    return result 

def inv_shift_rows(matrix):
    result = []
    for i in range(4):
        row = BitVector(size=0)
        for cell in matrix[i]:
            row += cell
        shifted = row >> (8 * i)
        result.append([shifted[8 * j : 8 * (j + 1)] for j in range(4)])
    return result

def mix_column(m1, m2):
    result = []
    for i in range(4):
        row = []
        for j in range(4):
            cell_val = BitVector(size=8)
            for k in range(4):
                cell_val ^= m1[i][k].gf_multiply_modular(m2[k][j], modulus, 8)
            row.append(cell_val)
        result.append(row)
    return result 

def encrypte(matrix, key_matrix, round_no):
    new_matrix = substitute_matrix_bytes(matrix)
    new_matrix = shift_rows(new_matrix) 
    if round_no != 9:
        new_matrix = mix_column(new_matrix, bvd.Mixer)
    new_matrix = xor_round_key(new_matrix, key_matrix)
    return new_matrix

def decrypte(matrix, key_matrix, round_no): 
    new_matrix = inv_shift_rows(matrix)
    new_matrix = inverse_substitute_matrix_bytes(new_matrix)
    new_matrix = xor_round_key(new_matrix, key_matrix)
    if round_no != 0:
        new_matrix = mix_column(new_matrix, bvd.InvMixer)
    return new_matrix