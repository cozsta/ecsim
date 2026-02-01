import random
import hashlib
from crypto_math import CURVE_SECP256K1, CURVE_P256, CURVE_VENSASAFE_256, make_keypair, sign_message, verify_safecurves

# --- "Файловая система" VensaSIM (глобальные переменные) ---
# EF_ICCID: Уникальный идентификатор карты
EF_ICCID = "8986044000000000001F" # Пример ICCID

# EF_VENSA_KEYS: Секретные приватные ключи (хранятся как (приватный_ключ, публичный_ключ))
# В реальной SIM это было бы защищено аппаратно. Здесь - просто в памяти.
EF_VENSA_KEYS = {
    "secp256k1": None,
    "P-256": None,
    "VensaSafe-256": None,
}

# EF_VENSA_PUBS: Публичные ключи (только публичные части)
EF_VENSA_PUBS = {
    "secp256k1": None,
    "P-256": None,
    "VensaSafe-256": None,
}

# EF_VENSA_CAPS: Список поддерживаемых кривых
EF_VENSA_CAPS = ["secp256k1", "P-256", "VensaSafe-256"]

# EF_VENSA_CONF: Текущая выбранная кривая для аутентификации
EF_VENSA_CONF = "secp256k1" # По умолчанию

# --- "VensaApplet" логика (функции) ---

def init_vensasim():
    """Инициализирует VensaSIM: генерирует ключи и заполняет "файловую систему"""
    print("VensaSIM: Инициализация карты...")
    # Генерируем ключи для доступных кривых
    curves = {
        "secp256k1": CURVE_SECP256K1,
        "P-256": CURVE_P256,
        "VensaSafe-256": CURVE_VENSASAFE_256
    }
    for name, params in curves.items():
        priv_key, pub_key = make_keypair(params)
        EF_VENSA_KEYS[name] = (priv_key, pub_key)
        EF_VENSA_PUBS[name] = pub_key
        print(f"VensaSIM: Сгенерирован ключ {name}. Публичный ключ: ({pub_key[0]:x}, {pub_key[1]:x})")

    print(f"VensaSIM: ICCID: {EF_ICCID}")
    print(f"VensaSIM: Поддерживаемые кривые: {EF_VENSA_CAPS}")
    print(f"VensaSIM: Активная кривая: {EF_VENSA_CONF}")

def process_apdu(command_apdu):
    """
    Главная функция VensaSIM, обрабатывающая APDU команды от модема.
    command_apdu - это строка, имитирующая APDU команду.
    Формат: "COMMAND_NAME:PARAM1:PARAM2:..."
    """
    print(f"\nVensaSIM: Получена APDU команда: {command_apdu}")
    parts = command_apdu.split(':')
    command = parts[0]

    if command == "SELECT_APPLET":
        return select_applet()
    elif command == "AUTHENTICATE":
        rand_hex = parts[1]
        curve_name = parts[2]
        return authenticate(rand_hex, curve_name)
    elif command == "READ_FILE":
        file_id = parts[1]
        return read_file(file_id)
    elif command == "SET_ACTIVE_CURVE":
        new_curve = parts[1]
        return set_active_curve(new_curve)
    else:
        return "ERROR:UNKNOWN_COMMAND"

def select_applet():
    """Обрабатывает команду SELECT_APPLET."""
    print("VensaSIM: Апплет VensaSIM выбран.")
    return "OK:VensaSIM_SELECTED"

def authenticate(rand_hex, curve_name):
    """
    Обрабатывает команду AUTHENTICATE: подписывает RAND выбранной кривой.
    rand_hex - строка HEX-представления RAND.
    curve_name - имя кривой для подписи.
    """
    global EF_VENSA_CONF # Возможно, понадобится для проверки активной кривой

    if curve_name not in EF_VENSA_CAPS:
        print(f"VensaSIM: Ошибка! Кривая {curve_name} не поддерживается.")
        return "ERROR:UNSUPPORTED_CURVE"
    
    if curve_name != EF_VENSA_CONF:
        print(f"VensaSIM: Внимание! Запрос на подпись кривой {curve_name}, но активна {EF_VENSA_CONF}.")
        # В реальной SIM это может быть ошибкой или требовать подтверждения.
        # Для PoC мы просто используем запрошенную кривую.

    private_key_data = EF_VENSA_KEYS.get(curve_name)
    if private_key_data is None:
        print(f"VensaSIM: Ошибка! Приватный ключ для {curve_name} не найден.")
        return "ERROR:KEY_NOT_FOUND"

    # Получаем параметры кривой
    curve_params = None
    if curve_name == "secp256k1": curve_params = CURVE_SECP256K1
    elif curve_name == "P-256": curve_params = CURVE_P256
    elif curve_name == "VensaSafe-256": curve_params = CURVE_VENSASAFE_256

    if not curve_params:
         return "ERROR:INVALID_CURVE_PARAMS"

    # ПРОВЕРКА SAFECURVES ПЕРЕД ПОДПИСЬЮ (Идеология VensaSIM)
    if not verify_safecurves(curve_params):
        print(f"VensaSIM: ПОДПИСЬ ЗАБЛОКИРОВАНА! Кривая {curve_name} не прошла проверку суверенитета.")
        return "ERROR:INSECURE_CURVE"

    priv_key, _ = private_key_data
    rand_bytes = bytes.fromhex(rand_hex)
    message_hash = int(hashlib.sha256(rand_bytes).hexdigest(), 16) # Хешируем RAND

    # Используем твою функцию подписи
    signature = sign_message(priv_key, message_hash, curve_params)
    
    # Преобразуем подпись (r, s) в HEX-строку для передачи
    signature_hex = f"{signature[0]:x}:{signature[1]:x}"
    print(f"VensaSIM: RAND подписан кривой {curve_name}. Подпись: {signature_hex}")
    return f"OK:SIGNATURE:{signature_hex}"

def read_file(file_id):
    """Читает содержимое "файла"."""
    if file_id == "EF_ICCID":
        return f"OK:DATA:{EF_ICCID}"
    elif file_id == "EF_VENSA_CAPS":
        return f"OK:DATA:{','.join(EF_VENSA_CAPS)}"
    elif file_id == "EF_VENSA_PUBS":
        pub_keys_str = []
        for curve_name, pub_key in EF_VENSA_PUBS.items():
            if pub_key:
                pub_keys_str.append(f"{curve_name}:{pub_key[0]:x}:{pub_key[1]:x}")
        return f"OK:DATA:{';'.join(pub_keys_str)}"
    elif file_id == "EF_VENSA_CONF":
        return f"OK:DATA:{EF_VENSA_CONF}"
    else:
        return "ERROR:FILE_NOT_FOUND"

def set_active_curve(new_curve_name):
    """Устанавливает активную кривую для аутентификации."""
    global EF_VENSA_CONF
    if new_curve_name in EF_VENSA_CAPS:
        EF_VENSA_CONF = new_curve_name
        print(f"VensaSIM: Активная кривая установлена на {new_curve_name}.")
        return "OK:CURVE_SET"
    else:
        print(f"VensaSIM: Ошибка! Кривая {new_curve_name} не поддерживается.")
        return "ERROR:UNSUPPORTED_CURVE"
