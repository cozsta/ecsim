#!/usr/bin/env python3
"""
VensaSIM Protocol Demo - Hackathon Edition
Live demonstration of cryptographic sovereignty in mobile networks
"""

import vensasim_emulator
import modem_emulator
import network_emulator
import time
import sys

# ANSI color codes for terminal
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{text.center(70)}{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}{'='*70}{Colors.ENDC}\n")

def print_step(step_num, text):
    print(f"{Colors.BOLD}{Colors.BLUE}[STEP {step_num}]{Colors.ENDC} {text}")
    time.sleep(0.5)

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")

def print_info(text):
    print(f"{Colors.YELLOW}→ {text}{Colors.ENDC}")

def simulate_network_delay(operation="Processing"):
    """Simulate realistic network latency"""
    print(f"{Colors.CYAN}  {operation}...", end='', flush=True)
    for _ in range(3):
        time.sleep(0.3)
        print(".", end='', flush=True)
    print(f" Done{Colors.ENDC}")
    time.sleep(0.2)

def run_auth_flow(iccid, selected_curve, pub_keys, demo_mode=True):
    """
    Execute authentication flow with visual feedback
    """
    print(f"\n{Colors.BOLD}┌─ AUTHENTICATION FLOW: {selected_curve.upper()} ─────────────────┐{Colors.ENDC}")
    
    # Step 1: Network generates challenge
    print_info("Network generating challenge (RAND)...")
    time.sleep(0.5)
    rand_from_network = network_emulator.generate_challenge(iccid, selected_curve)
    if rand_from_network is None:
        print_error(f"Network failed to generate challenge for {selected_curve}")
        return False
    print_success(f"Challenge generated: {rand_from_network[:16]}...")
    time.sleep(0.3)
    
    # Step 2: Modem requests signature from VensaSIM
    print_info("Modem → VensaSIM: AUTHENTICATE request")
    time.sleep(0.5)
    simulate_network_delay("VensaSIM signing")
    
    modem_response = modem_emulator.send_apdu_to_vensasim(f"AUTHENTICATE:{rand_from_network}:{selected_curve}")
    
    if "OK:SIGNATURE" in modem_response:
        signature_hex = modem_response.split(':')[2] + ":" + modem_response.split(':')[3]
        print_success(f"Signature received: {signature_hex[:32]}...")
        time.sleep(0.3)
        
        # Step 3: Network verifies signature
        print_info("Network verifying signature...")
        time.sleep(0.5)
        simulate_network_delay("Cryptographic verification")
        
        is_authenticated = network_emulator.verify_subscriber_signature(
            iccid, rand_from_network, signature_hex, selected_curve
        )
        
        if is_authenticated:
            print(f"{Colors.BOLD}{Colors.GREEN}╰─ AUTHENTICATION SUCCESS ✓{Colors.ENDC}")
        else:
            print(f"{Colors.BOLD}{Colors.RED}╰─ AUTHENTICATION FAILED ✗{Colors.ENDC}")
        
        time.sleep(0.5)
        return is_authenticated
    else:
        print_error(f"VensaSIM rejected signing: {modem_response}")
        print(f"{Colors.BOLD}{Colors.RED}╰─ AUTHENTICATION BLOCKED{Colors.ENDC}")
        time.sleep(0.5)
        return False

def main():
    """Main demonstration flow"""
    
    # Banner
    print_header("VENSASIM PROTOCOL DEMONSTRATION")
    print(f"{Colors.BOLD}Cryptographic Sovereignty for Mobile Networks{Colors.ENDC}")
    print(f"Hackathon Edition - Live Demo\n")
    time.sleep(1)
    
    # Initialize VensaSIM
    print_step(1, "Initializing VensaSIM secure element...")
    time.sleep(0.5)
    vensasim_emulator.init_vensasim()
    print()
    time.sleep(1)
    
    # Select applet
    print_step(2, "Modem connecting to VensaSIM applet...")
    time.sleep(0.5)
    modem_response = modem_emulator.send_apdu_to_vensasim("SELECT_APPLET")
    if "OK" in modem_response:
        print_success("VensaSIM applet selected")
    time.sleep(0.5)
    
    # Read ICCID
    print_step(3, "Reading SIM identification (ICCID)...")
    time.sleep(0.5)
    iccid_resp = modem_emulator.send_apdu_to_vensasim("READ_FILE:EF_ICCID")
    iccid = iccid_resp.split(':')[2]
    print_success(f"ICCID: {iccid}")
    time.sleep(0.5)
    
    # Read public keys
    print_step(4, "Reading public keys for all supported curves...")
    time.sleep(0.5)
    pubs_resp = modem_emulator.send_apdu_to_vensasim("READ_FILE:EF_VENSA_PUBS")
    pub_keys_raw = pubs_resp.split(':', 2)[2]
    parsed_pub_keys = {}
    
    for entry in pub_keys_raw.split(';'):
        if entry:
            c, x, y = entry.split(':')
            parsed_pub_keys[c] = (int(x, 16), int(y, 16))
    
    print_success(f"Loaded {len(parsed_pub_keys)} curve(s):")
    for curve_name in parsed_pub_keys.keys():
        print(f"  • {curve_name}")
        time.sleep(0.2)
    time.sleep(0.5)
    
    # Register with network
    print_step(5, "Registering subscriber with network...")
    time.sleep(0.5)
    simulate_network_delay("Network registration")
    network_emulator.register_subscriber(iccid, parsed_pub_keys)
    print_success(f"Subscriber {iccid} registered")
    time.sleep(1)
    
    # Main authentication demonstration
    print_header("AUTHENTICATION DEMONSTRATION")
    print(f"{Colors.BOLD}Testing authentication with default curve: secp256k1{Colors.ENDC}\n")
    time.sleep(1)
    
    # Demo with secp256k1 (default)
    selected_curve = "secp256k1"
    success = run_auth_flow(iccid, selected_curve, parsed_pub_keys, demo_mode=True)
    
    time.sleep(1)
    
    # Final result
    if success:
        print_header("✓ AUTHENTICATION SUCCESSFUL")
        print(f"{Colors.GREEN}{Colors.BOLD}User authenticated successfully using {selected_curve.upper()}{Colors.ENDC}")
        print(f"{Colors.GREEN}Network access granted{Colors.ENDC}")
    else:
        print_header("✗ AUTHENTICATION FAILED")
        print(f"{Colors.RED}{Colors.BOLD}Authentication blocked{Colors.ENDC}")
        print(f"{Colors.RED}Network access denied{Colors.ENDC}")
    
    print()
    time.sleep(0.5)
    
    # Show available curves
    print(f"\n{Colors.BOLD}Available curves for authentication:{Colors.ENDC}")
    curves_info = vensasim_emulator.EF_VENSA_CAPS
    for i, curve in enumerate(curves_info, 1):
        if curve == selected_curve:
            print(f"  {i}. {Colors.GREEN}✓ {curve} (currently used){Colors.ENDC}")
        else:
            print(f"  {i}.   {curve}")
        time.sleep(0.1)
    
    print(f"\n{Colors.CYAN}{'─'*70}{Colors.ENDC}")
    print(f"{Colors.BOLD}Demo completed. Ready for questions!{Colors.ENDC}")
    print(f"{Colors.CYAN}{'─'*70}{Colors.ENDC}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Colors.YELLOW}Demo interrupted by user{Colors.ENDC}")
        sys.exit(0)
