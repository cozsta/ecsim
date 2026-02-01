# main.py - Демонстрация Суверенного Протокола VensaSIM

import vensasim_emulator
import modem_emulator
import network_emulator
import hashlib

def run_auth_flow(iccid, selected_curve, pub_keys):
    print(f"\n--- [ПОТОК АУТЕНТИФИКАЦИИ: {selected_curve}] ---")
    
    # Сеть генерирует RAND
    rand_from_network = network_emulator.generate_challenge(iccid, selected_curve)
    if rand_from_network is None:
        print(f"СЕТЬ: Ошибка генерации вызова для {selected_curve}")
        return False

    # Модем запрашивает подпись у VensaSIM
    modem_response = modem_emulator.send_apdu_to_vensasim(f"AUTHENTICATE:{rand_from_network}:{selected_curve}")
    
    if "OK:SIGNATURE" in modem_response:
        signature_hex = modem_response.split(':')[2] + ":" + modem_response.split(':')[3]
        print(f"МОДЕМ: Получена подпись: {signature_hex}")
        
        # Верификация
        is_authenticated = network_emulator.verify_subscriber_signature(iccid, rand_from_network, signature_hex, selected_curve)
        return is_authenticated
    else:
        print(f"МОДЕМ: VensaSIM отказала в подписи ({modem_response})")
        return False

# --- Основной сценарий ---

print("--- ЗАПУСК VENSA-AKA PROTOCOL: GLASSED MODULE VERSION ---")

vensasim_emulator.init_vensasim()

# 1. Читаем данные через модем
modem_response = modem_emulator.send_apdu_to_vensasim("SELECT_APPLET")
iccid_resp = modem_emulator.send_apdu_to_vensasim("READ_FILE:EF_ICCID")
iccid = iccid_resp.split(':')[2]

pubs_resp = modem_emulator.send_apdu_to_vensasim("READ_FILE:EF_VENSA_PUBS")
pub_keys_raw = pubs_resp.split(':', 2)[2]
parsed_pub_keys = {}
for entry in pub_keys_raw.split(';'):
    if entry:
        c, x, y = entry.split(':')
        parsed_pub_keys[c] = (int(x, 16), int(y, 16))

# 2. Регистрация в сети
network_emulator.register_subscriber(iccid, parsed_pub_keys)

# 3. ТЕСТ 1: Попытка использовать "компрометированную" secp256k1 (Биткоин-кривая)
print("\n>>> ТЕСТ 1: Попытка входа через secp256k1 (Backdoor-166 detection)")
run_auth_flow(iccid, "secp256k1", parsed_pub_keys)

# 4. ТЕСТ 2: Попытка использовать "государственную" P-256 (NIST)
print("\n>>> ТЕСТ 2: Попытка входа через NIST P-256 (Opaque seed detection)")
run_auth_flow(iccid, "P-256", parsed_pub_keys)

# 5. ТЕСТ 3: Успешный вход через VensaSafe-256 (Sovereign-approved)
print("\n>>> ТЕСТ 3: Вход через VensaSafe-256 (Nothing-up-my-sleeve)")
success = run_auth_flow(iccid, "VensaSafe-256", parsed_pub_keys)

if success:
    print("\n[!] АУТЕНТИФИКАЦИЯ УСПЕШНА. СУВЕРЕНИТЕТ ПОДТВЕРЖДЕН.")
else:
    print("\n[!] КРИТИЧЕСКАЯ ОШИБКА ПРОТОКОЛА.")

print("\n--- Демонстрация завершена ---")
