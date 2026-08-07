import json
import random
import time
import threading
import paho.mqtt.client as mqtt

def sensor_worker(sensor_id):

    caminho_arquivo = f"config/sensor_{sensor_id}.json"

    with open(caminho_arquivo, "r") as arquivo:
        config = json.load(arquivo)

    print(config)

    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    client.connect(
        config["broker_ip"],
        config["broker_porta"]
    )

    client.loop_start()

    print(f"[SENSOR {sensor_id}] Conectado ao broker.")

# Anomalias
    while True:
        eh_anomalia = random.random() < 0.01

        if eh_anomalia:
            temp = random.uniform(61.0, 80.0)
        else:
            temp = config["base_temp"] + random.uniform(-1.0, 1.0)


        dados = {
            "sensor_id": sensor_id,
            "tipo": config["tipo"],
            "temperatura": round(temp, 2),
            "anomalia": eh_anomalia
        }

        mensagem = json.dumps(dados)

        topico = f"factory/sensors/{sensor_id}"

        client.publish(topico, mensagem)

        print(f"[SENSOR {sensor_id}] {mensagem}")
        
        time.sleep(config["intervalo_envio_s"])


if __name__ == "__main__":

    try:
        threads = []

        for sensor_id in range(1, 31):
            thread = threading.Thread(
                target=sensor_worker,
                args=(sensor_id,),
                daemon=True
            )

            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()


    except:
        print('\n[*]Smart Gateway finalizado pelo operador.')