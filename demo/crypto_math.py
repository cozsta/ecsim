# /Users/const/Downloads/ecsim/crypto_math.py

import collections
import random
import hashlib

# --- Параметры secp256k1 ---
_P_SECP256K1 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_N_SECP256K1 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_GX_SECP256K1 = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDb2DCE28D959F2815B16F81798
_GY_SECP256K1 = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

EllipticCurve = collections.namedtuple('EllipticCurve', 'name p a b g n h')

CURVE_SECP256K1 = EllipticCurve(
    'secp256k1',
    p=_P_SECP256K1,
    a=0,
    b=7,
    g=(_GX_SECP256K1, _GY_SECP256K1),
    n=_N_SECP256K1,
    h=1,
)

# --- Параметры NIST P-256 (secp256r1) - Считается "подозрительной" в VensaSIM ---
_P_P256 = 0xFFFFFFFF00000001000000000000000000000000FFFFFFFFFFFFFFFFFFFFFFFF
_N_P256 = 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551
_GX_P256 = 0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296
_GY_P256 = 0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5

CURVE_P256 = EllipticCurve(
    'P-256',
    p=_P_P256,
    a=-3 % _P_P256,
    b=0x5AC635D8AA3A93E7B3EBBD55769886BC651D06B0CC53B0F63BCE3C3E27D2604B,
    g=(_GX_P256, _GY_P256),
    n=_N_P256,
    h=1,
)

# --- Параметры VensaSafe-256 (secp256k1 base with Sovereign Generator) ---
_GX_VENSA = 0xed9abdbaffc855e92eae58a67e370589c64a7923a28d67305fa36ab8756072fd
_GY_VENSA = 0xdefd24bebe920b4f8415afdfdb162895a6ff8b02bb6b098062a78c3a22436836

CURVE_VENSASAFE_256 = EllipticCurve(
    'VensaSafe-256',
    p=_P_SECP256K1,
    a=0,
    b=7,
    g=(_GX_VENSA, _GY_VENSA),
    n=_N_SECP256K1,
    h=1,
)

def inverse_mod(k, p):
    if k == 0: raise ZeroDivisionError('division by zero')
    if k < 0: return p - inverse_mod(-k, p)
    s, old_s = 0, 1; t, old_t = 1, 0; r, old_r = p, k
    while r != 0:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
        old_t, t = t, old_t - quotient * t
    gcd, x, y = old_r, old_s, old_t
    assert gcd == 1
    return x % p

def is_on_curve(point, curve_params):
    if point is None: return True
    x, y = point
    return (y * y - x * x * x - curve_params.a * x - curve_params.b) % curve_params.p == 0

def point_neg(point, curve_params):
    if point is None: return None
    x, y = point
    result = (x, -y % curve_params.p)
    assert is_on_curve(result, curve_params)
    return result

def point_add(point1, point2, curve_params):
    if point1 is None: return point2
    if point2 is None: return point1
    x1, y1 = point1
    x2, y2 = point2

    # Case 1: point1 == point2 (doubling)
    if x1 == x2 and y1 == y2:
        if y1 == 0: # Tangent is vertical, result is point at infinity
            return None
        m = (3 * x1 ** 2 + curve_params.a) * inverse_mod(2 * y1, curve_params.p)
    # Case 2: point1 == -point2 (result is point at infinity)
    elif x1 == x2 and y1 != y2: # This means y1 == -y2 (mod p)
        return None
    # Case 3: point1 != point2 and point1 != -point2 (general addition)
    else:
        m = (y1 - y2) * inverse_mod(x1 - x2, curve_params.p)

    x3 = (m * m - x1 - x2) % curve_params.p
    # ИСПРАВЛЕНИЕ: Формула для y3 была неверна
    y3 = (m * (x1 - x3) - y1) % curve_params.p
    result = (x3, y3 % curve_params.p) # y3 уже с правильным знаком, не нужно -y3
    assert is_on_curve(result, curve_params)
    return result

def scalar_mult(k, point, curve_params):
    if k % curve_params.n == 0 or point is None:
        return None
    if k < 0: return scalar_mult(-k, point_neg(point, curve_params), curve_params)

    result = None
    addend = point
    while k:
        if k & 1:
            result = point_add(result, addend, curve_params)
        addend = point_add(addend, addend, curve_params)
        k >>= 1
    assert is_on_curve(result, curve_params)
    return result

def make_keypair(curve_params):
    private_key = random.randrange(1, curve_params.n)
    public_key = scalar_mult(private_key, curve_params.g, curve_params)
    return private_key, public_key

def _generate_k_rfc6979(private_key, message_hash, curve_params):
    priv_bytes = private_key.to_bytes(32, 'big')
    msg_hash_bytes = message_hash.to_bytes(32, 'big')
    
    seed = hashlib.sha256(priv_bytes + msg_hash_bytes).digest()
    k = int.from_bytes(seed, 'big') % (curve_params.n - 1) + 1
    
    if k == 0:
        k = 1 
    
    return k

def sign_message(private_key, message_hash, curve_params):
    n = curve_params.n
    G = curve_params.g

    k = _generate_k_rfc6979(private_key, message_hash, curve_params)
    
    R = scalar_mult(k, G, curve_params)
    if R is None:
        raise ValueError("R is point at infinity during signing")

    r = R[0] % n
    if r == 0:
        raise ValueError("r=0 during signing")

    k_inv = inverse_mod(k, n)

    s = (k_inv * (message_hash + r * private_key)) % n
    if s == 0:
        raise ValueError("s=0 during signing")

    print(f"DEBUG: Сообщение подписано. r={hex(r)}, s={hex(s)}")
    return (r, s)

# --- SafeCurves Verification (Идеологический фильтр VensaSIM) ---

def verify_safecurves(curve):
    """
    Проверяет кривую на соответствие критериям SafeCurves (упрощенно).
    """
    print(f"SafeCurves: Проверка кривой {curve.name}...")
    
    # 1. Rho Hardness (Large Prime n)
    if curve.n.bit_length() < 250:
        print(f"SafeCurves [FAIL]: Порядок n слишком мал ({curve.n.bit_length()} бит).")
        return False
        
    # 2. X-Coordinate Anomalies (VensaSIM Exclusive check)
    # Тот самый "бэкдор" в 166 бит
    half_point = scalar_mult((curve.n - 1) // 2, curve.g, curve)
    if half_point[0].bit_length() < 200:
        print(f"SafeCurves [FAIL]: Обнаружена аномалия x-координаты (Backdoor-166). Bit length: {half_point[0].bit_length()}")
        return False

    # 3. Rigidity check (Dummy for PoC)
    if curve.name == 'P-256':
        print(f"SafeCurves [FAIL]: Кривая {curve.name} выбрана непрозрачно (NIST seed).")
        return False

    print(f"SafeCurves [PASS]: Кривая {curve.name} прошла проверку.")
    return True

def verify_signature(public_key, message_hash, signature, curve_params):
    n = curve_params.n
    G = curve_params.g

    r, s = signature

    if not (1 <= r <= n - 1) or not (1 <= s <= n - 1):
        print(f"DEBUG: Верификация провалена: r или s вне диапазона. r={r}, s={s}")
        return False

    s_inv = inverse_mod(s, n)

    u1 = (message_hash * s_inv) % n
    u2 = (r * s_inv) % n

    P1 = scalar_mult(u1, G, curve_params)
    P2 = scalar_mult(u2, public_key, curve_params)
    
    P = point_add(P1, P2, curve_params)

    if P is None:
        print("DEBUG: Верификация провалена: P - точка на бесконечности.")
        return False

    is_valid = (P[0] % n == r)
    print(f"DEBUG: Верификация завершена. P.x % n = {P[0] % n}, r = {r}. Результат: {is_valid}")
    return is_valid
