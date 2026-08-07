import json

tipos_sensores = [
    ("temperatura_caldeira", 25.0),
    ("temperatura_estufa", 40.0),
    ("temperatura_camara_fria", -5.0),
    ("temperatura_motor", 35.0),
    ("temperatura_forno", 50.0)
]

for sensor_id in range(1, 31):

    tipo, base_temp = tipos_sensores[(sensor_id - 1) % len(tipos_sensores)]

    config = {
        "id": sensor_id,
        "tipo": tipo,
        "base_temp": base_temp,
        "broker_ip": "127.0.0.1",
        "broker_porta": 1883,
        "intervalo_envio_s": 0.1
    }

    caminho = f"config/sensor_{sensor_id}.json"

    with open(caminho, "w") as arquivo:
        json.dump(config, arquivo, indent=4)

    print(f"Criado: {caminho}")