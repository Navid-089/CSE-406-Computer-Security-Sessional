import Crypto.Util.number

def gcd(a, b):
    return a if b == 0 else gcd(b, a % b)

def mod_pow(base, exponent, modulus):
    if exponent == 0:
        return 1
    half = mod_pow(base, exponent // 2, modulus) % modulus
    result = (half * half) % modulus
    return (base * result) % modulus if exponent % 2 else result 

def mod_inverse(a, modulus):
    if gcd(a, modulus) != 1:
        raise ValueError(f"No modular inverse for {a} mod {modulus}")
    return mod_pow(a, modulus - 2, modulus) 

def generate_curve_params(key_bits):
    while True:
        a = Crypto.Util.number.getRandomNBitInteger(key_bits) % (1 << key_bits)
        gx = Crypto.Util.number.getRandomNBitInteger(key_bits)
        gy = Crypto.Util.number.getRandomNBitInteger(key_bits)
        g = (gx, gy)
        p = Crypto.Util.number.getPrime(key_bits)
        b = (gy**2 - gx**3 - a * gx) % p
        if (4 * a**3 + 27 * b**2) % p != 0:
            return a, b, g, p
        
def ecc_point_double(point, a, p):
    slope = ((3 * point[0]**2 + a) * mod_inverse(2 * point[1], p)) % p
    x3 = (slope**2 - 2 * point[0]) % p
    y3 = (slope * (point[0] - x3) - point[1]) % p
    return (x3, y3) 

def ecc_point_add(p1, p2, p):
    slope = ((p2[1] - p1[1]) * mod_inverse(p2[0] - p1[0], p)) % p
    x3 = (slope**2 - p1[0] - p2[0]) % p
    y3 = (slope * (p1[0] - x3) - p1[1]) % p
    return (x3, y3)

def ecc_scalar_mult(k, point, a, p):
    result = None
    for bit in bin(k)[2:]:
        if result is None:
            result = point
        else:
            result = ecc_point_double(result, a, p)
        if bit == "1" and result != point:
            result = ecc_point_add(result, point, p)
    return result