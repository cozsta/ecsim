"""
VensaSIM Secure Element Emulator
Hackathon Demo Edition - English Version
"""

import random
import hashlib
from crypto_math import (
    CURVE_SECP256K1, CURVE_ED25519, CURVE_BLS12_381, CURVE_CUSTOM,
    SUPPORTED_CURVES, make_keypair, sign_message, get_curve_by_name
)

# ============================================================================
# VENSASIM FILE SYSTEM (Simulated Secure Storage)
# ============================================================================

# ICCID - SIM Card Identifier
EF_ICCID = "8986044000000000001F"

# Private keys storage (in real SIM this is hardware-protected)
EF_VENSA_KEYS = {
    "secp256k1": None,
    "ed25519": None,
    "bls12-381": None,
    "custom": None,
}

# Public keys (can be exported)
EF_VENSA_PUBS = {
    "secp256k1": None,
    "ed25519": None,
    "bls12-381": None,
    "custom": None,
}

# Supported curves list
EF_VENSA_CAPS = ["secp256k1", "ed25519", "bls12-381", "custom"]

# Current active curve
EF_VENSA_CONF = "secp256k1"

# ============================================================================
# VENSASIM APPLET LOGIC
# ============================================================================

def init_vensasim(silent=False):
    """Initialize VensaSIM: generate keys for all supported curves"""
    if not silent:
        print("VensaSIM: Initializing secure element...")
    
    for curve_name in EF_VENSA_CAPS:
        curve = get_curve_by_name(curve_name)
        if curve:
            priv_key, pub_key = make_keypair(curve)
            EF_VENSA_KEYS[curve_name] = (priv_key, pub_key)
            EF_VENSA_PUBS[curve_name] = pub_key
            if not silent:
                print(f"  ✓ Generated keypair for {curve_name}")
    
    if not silent:
        print(f"  ICCID: {EF_ICCID}")
        print(f"  Supported curves: {EF_VENSA_CAPS}")
        print(f"  Active curve: {EF_VENSA_CONF}")

def process_apdu(command_apdu, silent=False):
    """
    Main APDU command processor
    Format: "COMMAND:PARAM1:PARAM2:..."
    """
    parts = command_apdu.split(':')
    command = parts[0]

    if command == "SELECT_APPLET":
        return select_applet(silent)
    elif command == "AUTHENTICATE":
        rand_hex = parts[1]
        curve_name = parts[2]
        return authenticate(rand_hex, curve_name, silent)
    elif command == "READ_FILE":
        file_id = parts[1]
        return read_file(file_id, silent)
    elif command == "SET_ACTIVE_CURVE":
        new_curve = parts[1]
        return set_active_curve(new_curve, silent)
    else:
        return "ERROR:UNKNOWN_COMMAND"

def select_applet(silent=False):
    """Handle SELECT_APPLET command"""
    if not silent:
        print("  VensaSIM: Applet selected")
    return "OK:VENSASIM_SELECTED"

def authenticate(rand_hex, curve_name, silent=False):
    """
    Handle AUTHENTICATE command: sign RAND with specified curve
    """
    global EF_VENSA_CONF

    if curve_name not in EF_VENSA_CAPS:
        return "ERROR:UNSUPPORTED_CURVE"
    
    private_key_data = EF_VENSA_KEYS.get(curve_name)
    if private_key_data is None:
        return "ERROR:KEY_NOT_FOUND"

    curve = get_curve_by_name(curve_name)
    if not curve:
        return "ERROR:INVALID_CURVE"

    priv_key, _ = private_key_data
    rand_bytes = bytes.fromhex(rand_hex)
    message_hash = int(hashlib.sha256(rand_bytes).hexdigest(), 16)

    # Sign the challenge
    signature = sign_message(priv_key, message_hash, curve)
    signature_hex = f"{signature[0]:064x}:{signature[1]:064x}"
    
    if not silent:
        print(f"  VensaSIM: Challenge signed with {curve_name}")
    
    return f"OK:SIGNATURE:{signature_hex}"

def read_file(file_id, silent=False):
    """Read file from VensaSIM storage"""
    if file_id == "EF_ICCID":
        return f"OK:DATA:{EF_ICCID}"
    elif file_id == "EF_VENSA_CAPS":
        return f"OK:DATA:{','.join(EF_VENSA_CAPS)}"
    elif file_id == "EF_VENSA_PUBS":
        pub_keys_str = []
        for curve_name, pub_key in EF_VENSA_PUBS.items():
            if pub_key:
                pub_keys_str.append(f"{curve_name}:{pub_key[0]:064x}:{pub_key[1]:064x}")
        return f"OK:DATA:{';'.join(pub_keys_str)}"
    elif file_id == "EF_VENSA_CONF":
        return f"OK:DATA:{EF_VENSA_CONF}"
    else:
        return "ERROR:FILE_NOT_FOUND"

def set_active_curve(new_curve_name, silent=False):
    """Set the active curve for authentication"""
    global EF_VENSA_CONF
    if new_curve_name in EF_VENSA_CAPS:
        EF_VENSA_CONF = new_curve_name
        if not silent:
            print(f"  VensaSIM: Active curve set to {new_curve_name}")
        return "OK:CURVE_SET"
    else:
        return "ERROR:UNSUPPORTED_CURVE"
