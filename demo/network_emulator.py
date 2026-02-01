# network_emulator.py

import random
import hashlib
from crypto_math import CURVE_SECP256K1, CURVE_P256, CURVE_VENSASAFE_256, verify_signature

# --- "База данных" сети (глобальные переменные) ---
# Зарегистрированные публичные ключи абонентов
REGISTERED_PUBLIC_KEYS = {
    # "ICCID": {"curve_name": public_key_tuple}
}

def register_subscriber(iccid, pub_keys_data):
    """
    Регистрирует абонента в сети.
    pub_keys_data - словарь вида {"curve_name": (pub_x, pub_y)}
    """
    print(f"\nСеть: Регистрация абонента {iccid}...")
    REGISTERED_PUBLIC_KEYS[iccid] = pub_keys_data
    print(f"Сеть: Зарегистрированы публичные ключи: {pub_keys_data}")

def generate_challenge(iccid, curve_name):
    """Генерирует случайный RAND (вызов) для абонента и кривой."""
    if iccid not in REGISTERED_PUBLIC_KEYS:
        print(f"Сеть: Ошибка! Абонент {iccid} не зарегистрирован.")
        return None
    if curve_name not in REGISTERED_PUBLIC_KEYS[iccid]:
        print(f"Сеть: Ошибка! Абонент {iccid} не имеет ключа для кривой {curve_name}.")
        return None

    rand_bytes = random.getrandbits(256).to_bytes(32, 'big') # 32 байта случайных данных
    rand_hex = rand_bytes.hex()
    print(f"Сеть: Сгенерирован RAND для {iccid} ({curve_name}): {rand_hex}")
    return rand_hex

def verify_subscriber_signature(iccid, rand_hex, signature_hex, curve_name):
    """
    Проверяет подпись абонента.
    signature_hex - строка HEX-представления подписи "r:s".
    """
    print(f"\nСеть: Проверка подписи абонента {iccid}...")
    if iccid not in REGISTERED_PUBLIC_KEYS:
        print(f"Сеть: Ошибка! Абонент {iccid} не зарегистрирован.")
        return False
    
    public_key = REGISTERED_PUBLIC_KEYS[iccid].get(curve_name)
    if public_key is None:
        print(f"Сеть: Ошибка! Публичный ключ для {curve_name} не найден у абонента {iccid}.")
        return False

    rand_bytes = bytes.fromhex(rand_hex)
    message_hash = int(hashlib.sha256(rand_bytes).hexdigest(), 16)

    try:
        r_hex, s_hex = signature_hex.split(':')
        signature = (int(r_hex, 16), int(s_hex, 16))
    except ValueError:
        print("Сеть: Ошибка! Неверный формат подписи.")
        return False

    # Получаем параметры кривой
    curve_params = None
    if curve_name == "secp256k1": curve_params = CURVE_SECP256K1
    elif curve_name == "P-256": curve_params = CURVE_P256
    elif curve_name == "VensaSafe-256": curve_params = CURVE_VENSASAFE_256

    if not curve_params:
         print(f"Сеть: Ошибка! Неизвестная кривая {curve_name}.")
         return False

    # Используем твою функцию верификации
    is_valid = verify_signature(public_key, message_hash, signature, curve_params)
    
    if is_valid:
        print(f"Сеть: Подпись абонента {iccid} ВЕРНА! Аутентификация успешна.")
    else:
        print(f"Сеть: Подпись абонента {iccid} НЕВЕРНА! Аутентификация провалена.")
    return is_valid
