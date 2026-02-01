"""
VensaSIM Cryptographic Primitives
Hackathon Demo Edition - English Version
"""

import collections
import random
import hashlib

# ============================================================================
# CURVE DEFINITIONS
# ============================================================================

EllipticCurve = collections.namedtuple('EllipticCurve', 'name p a b g n h curve_type')

# --- secp256k1 (Bitcoin curve) - DEFAULT ---
_P_SECP256K1 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEFFFFFC2F
_N_SECP256K1 = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
_GX_SECP256K1 = 0x79BE667EF9DCBBAC55A06295CE870B07029BFCDb2DCE28D959F2815B16F81798
_GY_SECP256K1 = 0x483ADA7726A3C4655DA4FBFC0E1108A8FD17B448A68554199C47D08FFB10D4B8

CURVE_SECP256K1 = EllipticCurve(
    name='secp256k1',
    p=_P_SECP256K1,
    a=0,
    b=7,
    g=(_GX_SECP256K1, _GY_SECP256K1),
    n=_N_SECP256K1,
    h=1,
    curve_type='weierstrass'
)

# --- Ed25519 (STUB - Edwards curve, different math) ---
# Real Ed25519 uses twisted Edwards form, this is a placeholder
_P_ED25519 = 2**255 - 19
_N_ED25519 = 2**252 + 27742317777372353535851937790883648493

CURVE_ED25519 = EllipticCurve(
    name='ed25519',
    p=_P_ED25519,
    a=-1,  # Edwards curve coefficient
    b=0,   # Not used for Edwards
    g=(0x216936D3CD6E53FEC0A4E231FDD6DC5C692CC7609525A7B2C9562D608F25D51A,
       0x6666666666666666666666666666666666666666666666666666666666666658),
    n=_N_ED25519,
    h=8,
    curve_type='edwards'
)

# --- BLS12-381 (STUB - Pairing-friendly curve for aggregation) ---
# Real BLS12-381 is much more complex, this is a placeholder
_P_BLS12_381 = 0x1a0111ea397fe69a4b1ba7b6434bacd764774b84f38512bf6730d2a0f6b0f6241eabfffeb153ffffb9feffffffffaaab

CURVE_BLS12_381 = EllipticCurve(
    name='bls12-381',
    p=_P_BLS12_381,
    a=0,
    b=4,
    g=(0x17F1D3A73197D7942695638C4FA9AC0FC3688C4F9774B905A14E3A3F171BAC586C55E83FF97A1AEFFB3AF00ADB22C6BB,
       0x08B3F481E3AAA0F1A09E30ED741D8AE4FCF5E095D5D00AF600DB18CB2C04B3EDD03CC744A2888AE40CAA232946C5E7E1),
    n=0x73eda753299d7d483339d80809a1d80553bda402fffe5bfeffffffff00000001,
    h=0x396C8C005555E1568C00AAAB0000AAAB,
    curve_type='bls'
)

# --- Custom Curve (Placeholder for user-defined) ---
CURVE_CUSTOM = EllipticCurve(
    name='custom',
    p=_P_SECP256K1,
    a=0,
    b=7,
    g=(_GX_SECP256K1, _GY_SECP256K1),
    n=_N_SECP256K1,
    h=1,
    curve_type='custom'
)

# Supported curves registry
SUPPORTED_CURVES = {
    'secp256k1': CURVE_SECP256K1,
    'ed25519': CURVE_ED25519,
    'bls12-381': CURVE_BLS12_381,
    'custom': CURVE_CUSTOM
}

# ============================================================================
# WEIERSTRASS CURVE MATH (for secp256k1)
# ============================================================================

def inverse_mod(k, p):
    if k == 0: raise ZeroDivisionError('division by zero')
    if k < 0: return p - inverse_mod(-k, p)
    s, old_s = 0, 1
    r, old_r = p, k
    while r != 0:
        quotient = old_r // r
        old_r, r = r, old_r - quotient * r
        old_s, s = s, old_s - quotient * s
    return old_s % p

def is_on_curve(point, curve):
    if point is None: return True
    x, y = point
    return (y * y - x * x * x - curve.a * x - curve.b) % curve.p == 0

def point_neg(point, curve):
    if point is None: return None
    x, y = point
    return (x, -y % curve.p)

def point_add(point1, point2, curve):
    if point1 is None: return point2
    if point2 is None: return point1
    x1, y1 = point1
    x2, y2 = point2

    if x1 == x2 and y1 == y2:
        if y1 == 0: return None
        m = (3 * x1 ** 2 + curve.a) * inverse_mod(2 * y1, curve.p)
    elif x1 == x2:
        return None
    else:
        m = (y1 - y2) * inverse_mod(x1 - x2, curve.p)

    x3 = (m * m - x1 - x2) % curve.p
    y3 = (m * (x1 - x3) - y1) % curve.p
    return (x3, y3)

def scalar_mult(k, point, curve):
    if k % curve.n == 0 or point is None:
        return None
    if k < 0: return scalar_mult(-k, point_neg(point, curve), curve)

    result = None
    addend = point
    while k:
        if k & 1:
            result = point_add(result, addend, curve)
        addend = point_add(addend, addend, curve)
        k >>= 1
    return result

# ============================================================================
# KEY GENERATION & SIGNATURES
# ============================================================================

def make_keypair(curve):
    """Generate a keypair for the given curve"""
    if curve.curve_type in ['edwards', 'bls']:
        # Stub: Generate random bytes and pretend it's a valid key
        private_key = random.randrange(1, curve.n)
        # For demo, we'll fake a public key point
        public_key = scalar_mult(private_key, curve.g, CURVE_SECP256K1)
        return private_key, public_key
    else:
        private_key = random.randrange(1, curve.n)
        public_key = scalar_mult(private_key, curve.g, curve)
        return private_key, public_key

def _generate_k_rfc6979(private_key, message_hash, curve):
    """Deterministic nonce generation per RFC6979"""
    priv_bytes = private_key.to_bytes(32, 'big')
    msg_bytes = message_hash.to_bytes(32, 'big')
    seed = hashlib.sha256(priv_bytes + msg_bytes).digest()
    k = int.from_bytes(seed, 'big') % (curve.n - 1) + 1
    return k

def sign_message(private_key, message_hash, curve):
    """Sign a message hash with ECDSA"""
    if curve.curve_type in ['edwards', 'bls']:
        # Stub signature for non-Weierstrass curves
        k = _generate_k_rfc6979(private_key, message_hash, CURVE_SECP256K1)
        R = scalar_mult(k, CURVE_SECP256K1.g, CURVE_SECP256K1)
        r = R[0] % CURVE_SECP256K1.n
        k_inv = inverse_mod(k, CURVE_SECP256K1.n)
        s = (k_inv * (message_hash + r * private_key)) % CURVE_SECP256K1.n
        return (r, s)
    
    n = curve.n
    G = curve.g
    k = _generate_k_rfc6979(private_key, message_hash, curve)
    
    R = scalar_mult(k, G, curve)
    if R is None:
        raise ValueError("R is point at infinity")

    r = R[0] % n
    if r == 0:
        raise ValueError("r=0 during signing")

    k_inv = inverse_mod(k, n)
    s = (k_inv * (message_hash + r * private_key)) % n
    if s == 0:
        raise ValueError("s=0 during signing")

    return (r, s)

def verify_signature(public_key, message_hash, signature, curve):
    """Verify an ECDSA signature"""
    if curve.curve_type in ['edwards', 'bls']:
        # Stub verification - always use secp256k1 math internally
        curve = CURVE_SECP256K1
    
    n = curve.n
    G = curve.g
    r, s = signature

    if not (1 <= r <= n - 1) or not (1 <= s <= n - 1):
        return False

    s_inv = inverse_mod(s, n)
    u1 = (message_hash * s_inv) % n
    u2 = (r * s_inv) % n

    P1 = scalar_mult(u1, G, curve)
    P2 = scalar_mult(u2, public_key, curve)
    P = point_add(P1, P2, curve)

    if P is None:
        return False

    return (P[0] % n == r)

def get_curve_by_name(name):
    """Get curve parameters by name"""
    return SUPPORTED_CURVES.get(name)
