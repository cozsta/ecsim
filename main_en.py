# /Users/const/Downloads/ecsim/main_en.py

import vensasim_emulator
import modem_emulator
import network_emulator
import hashlib

# --- Main demonstration scenario ---

print("--- Launching VensaSIM Sovereignty Protocol ---")

print("DEBUG: Calling vensasim_emulator.init_vensasim()")
vensasim_emulator.init_vensasim()
print(f"DEBUG: After initialization, vensasim_emulator.EF_VENSA_PUBS: {vensasim_emulator.EF_VENSA_PUBS}")

# 2. Modem "inserts" VensaSIM and selects applet
modem_response = modem_emulator.send_apdu_to_vensasim("SELECT_APPLET")
if "OK" not in modem_response:
    print("ERROR: Failed to select VensaSIM applet. Exiting.")
    exit()

# 3. Modem reads VensaSIM public data for network registration
# Read ICCID
modem_response = modem_emulator.send_apdu_to_vensasim("READ_FILE:EF_ICCID")
if "OK" in modem_response:
    iccid = modem_response.split(':')[2]
    print(f"Modem: Read ICCID: {iccid}")
else:
    print("ERROR: Failed to read ICCID. Exiting.")
    exit()

# Read public keys
modem_response = modem_emulator.send_apdu_to_vensasim("READ_FILE:EF_VENSA_PUBS")
if "OK" in modem_response:
    pub_keys_raw_data = modem_response.split(':', 2)[2]
    print(f"DEBUG: Raw public key data from VensaSIM: '{pub_keys_raw_data}'")
    parsed_pub_keys = {}
    if pub_keys_raw_data:
        for entry in pub_keys_raw_data.split(';'):
            print(f"DEBUG: Processing key entry: '{entry}'")
            if entry and ':' in entry and len(entry.split(':')) == 3:
                curve_name, x_hex, y_hex = entry.split(':')
                parsed_pub_keys[curve_name] = (int(x_hex, 16), int(y_hex, 16))
            else:
                print(f"ERROR: Skipping malformed or empty key entry: '{entry}'")
    else:
        print("ERROR: No public keys found in VensaSIM response.")
    
    if not parsed_pub_keys:
        print("ERROR: Failed to parse public keys. Exiting.")
        exit()

    print(f"Modem: Read and parsed public keys: {parsed_pub_keys}")
else:
    print("ERROR: Failed to read public keys from VensaSIM. Exiting.")
    exit()

# 4. Network registers the subscriber with their public keys
network_emulator.register_subscriber(iccid, parsed_pub_keys)

# 5. Network selects a curve and generates RAND (challenge)
selected_curve = "secp256k1" # Network selects the curve for authentication
rand_from_network = network_emulator.generate_challenge(iccid, selected_curve)
if rand_from_network is None:
    print("ERROR: Failed to generate RAND. Exiting.")
    exit()

# 6. Modem relays RAND to VensaSIM
modem_response = modem_emulator.send_apdu_to_vensasim(f"AUTHENTICATE:{rand_from_network}:{selected_curve}")
if "OK" in modem_response:
    signature_hex = modem_response.split(':')[2]
    print(f"Modem: Received signature from VensaSIM: {signature_hex}")
else:
    print("ERROR: VensaSIM failed to sign RAND. Exiting.")
    exit()

# 7. Modem relays signature to network for verification
is_authenticated = network_emulator.verify_subscriber_signature(iccid, rand_from_network, signature_hex, selected_curve)

if is_authenticated:
    print("\n--- AUTHENTICATION SUCCESSFUL! WELCOME TO THE SOVEREIGN NETWORK! ---")
else:
    print("\n--- AUTHENTICATION FAILED! GET THE FUCK OUT, SPY! ---")

print("\n--- Demonstration finished ---")