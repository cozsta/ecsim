"""
Network Emulator
Hackathon Demo Edition - English Version
"""

import random
import hashlib
from crypto_math import SUPPORTED_CURVES, verify_signature, get_curve_by_name

# ============================================================================
# NETWORK DATABASE
# ============================================================================

# Registered subscribers with their public keys
REGISTERED_PUBLIC_KEYS = {}

# Active challenges (RAND) per subscriber
ACTIVE_CHALLENGES = {}

# ============================================================================
# NETWORK OPERATIONS
# ============================================================================

def register_subscriber(iccid, pub_keys_data, silent=False):
    """
    Register a subscriber with their public keys
    pub_keys_data: dict {"curve_name": (pub_x, pub_y)}
    """
    REGISTERED_PUBLIC_KEYS[iccid] = pub_keys_data
    if not silent:
        print(f"  Network: Subscriber {iccid} registered with {len(pub_keys_data)} curve(s)")

def generate_challenge(iccid, curve_name, silent=False):
    """Generate a random challenge (RAND) for authentication"""
    if iccid not in REGISTERED_PUBLIC_KEYS:
        return None
    if curve_name not in REGISTERED_PUBLIC_KEYS[iccid]:
        return None

    rand_bytes = random.getrandbits(256).to_bytes(32, 'big')
    rand_hex = rand_bytes.hex()
    
    # Store active challenge
    ACTIVE_CHALLENGES[iccid] = (rand_hex, curve_name)
    
    if not silent:
        print(f"  Network: Challenge generated for {iccid}")
    
    return rand_hex

def verify_subscriber_signature(iccid, rand_hex, signature_hex, curve_name, silent=False):
    """
    Verify subscriber's signature
    signature_hex: "r:s" format
    """
    if iccid not in REGISTERED_PUBLIC_KEYS:
        return False
    
    public_key = REGISTERED_PUBLIC_KEYS[iccid].get(curve_name)
    if public_key is None:
        return False

    rand_bytes = bytes.fromhex(rand_hex)
    message_hash = int(hashlib.sha256(rand_bytes).hexdigest(), 16)

    try:
        r_hex, s_hex = signature_hex.split(':')
        signature = (int(r_hex, 16), int(s_hex, 16))
    except ValueError:
        return False

    curve = get_curve_by_name(curve_name)
    if not curve:
        return False

    is_valid = verify_signature(public_key, message_hash, signature, curve)
    
    if not silent:
        if is_valid:
            print(f"  Network: Signature VALID - Authentication successful")
        else:
            print(f"  Network: Signature INVALID - Authentication failed")
    
    return is_valid
