# modem_emulator.py

import vensasim_emulator # Модем общается с VensaSIM
# import network_emulator # Модем будет общаться с сетью (пока не реализовано)

def send_apdu_to_vensasim(command_apdu):
    """Модем отправляет APDU команду в VensaSIM и получает ответ."""
    print(f"\nМодем: Отправка APDU в VensaSIM: {command_apdu}")
    response = vensasim_emulator.process_apdu(command_apdu)
    print(f"Модем: Получен ответ от VensaSIM: {response}")
    return response

def relay_to_network(data):
    """Модем ретранслирует данные в сеть (заглушка)."""
    print(f"Модем: Ретрансляция данных в сеть: {data}")
    # В реальной жизни здесь будет сетевое взаимодействие с MNO Core Network
    # Пока просто возвращаем данные, чтобы их мог обработать network_emulator
    return data

def receive_from_network(data):
    """Модем получает данные из сети (заглушка)."""
    print(f"Модем: Получены данные из сети: {data}")
    # В реальной жизни здесь будет получение данных от MNO Core Network
    return data
