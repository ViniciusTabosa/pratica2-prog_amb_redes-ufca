import json
import threading
import time
import paho.mqtt.client as mqtt
import firebase_admin
from firebase_admin import credentials, db
import smtplib
from email.message import EmailMessage
from datetime import datetime

buffer_dados = []

lock = threading.Lock()

ultimo_alerta = 0
INTERVALO_ALERTA = 60

cred = credentials.Certificate("firebase_credentials.json")

firebase_admin.initialize_app(cred, {
    "databaseURL": "https://pratica2-par-ufca-default-rtdb.firebaseio.com/"
})

ref_estatisticas = db.reference("estatisticas")

with open("email_config.json", "r") as arquivo:
    email_config = json.load(arquivo)

def enviar_alerta_email(sensor_id, temperatura):
    mensagem = EmailMessage()

    mensagem["Subject"] = "ALERTA - Temperatura crítica"
    mensagem["From"] = email_config["email_remetente"]
    mensagem["To"] = email_config["email_destinatario"]

    mensagem.set_content(
        f"Alerta de temperatura crítica!\n\n"
        f"Sensor: {sensor_id}\n"
        f"Temperatura registrada: {temperatura} °C"
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
        servidor.login(
            email_config["email_remetente"],
            email_config["senha_app"]
        )

        servidor.send_message(mensagem)

    print("[EMAIL] Alerta enviado com sucesso!")

def ao_receber_mensagem(client, userdata, msg):

    global ultimo_alerta

    payload = msg.payload.decode()

    dados = json.loads(payload)

    temperatura = dados["temperatura"]

    with lock:
        buffer_dados.append(temperatura)

        if temperatura > 60:
            print(
                f"[ALERTA] Sensor {dados['sensor_id']} "
                f"registrou {temperatura} °C!"
            )

            agora = time.time()

            if agora - ultimo_alerta >= INTERVALO_ALERTA:
                enviar_alerta_email(
                    dados["sensor_id"],
                    temperatura
                )

                ultimo_alerta = agora
            else:
                print("[ALERTA] E-mail não enviado: limite de 1 minuto.")

        if temperatura > 60:
            horario_deteccao = datetime.now()

            print(
                f"[ALERTA] Sensor {dados['sensor_id']} "
                f"registrou {temperatura} °C às "
                f"{horario_deteccao.strftime('%H:%M:%S.%f')[:-3]}"
            )

        print(f"Recebido: Sensor {dados['sensor_id']} -> {temperatura} °C")

def thread_estatisticas():

    while True:
        time.sleep(1)

        with lock:
            if len(buffer_dados) == 0:
                continue

            quantidade = len(buffer_dados)
            media = sum(buffer_dados) / quantidade

            buffer_dados.clear()

        print(
            f"[ESTATÍSTICAS] Leituras: {quantidade} | "
            f"Média: {media:.2f} °C"
        )

        economia = ((quantidade - 1) / quantidade)*100

        print(
            f"[ECONOMIA DE BANDA] "
            f"{quantidade} mensagens locais -> 1 mensagem para a nuvem "
            f"Economia: {economia}"
        )

        ref_estatisticas.push({
            "media_temperatura": round(media, 2),
            "quantidade_leituras": quantidade,
            "timestamp": int(time.time())
        })

        
if __name__ == "__main__":
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

    client.on_message = ao_receber_mensagem

    client.connect("127.0.0.1", 1883)

    client.subscribe("factory/sensors/+")

    estatisticas = threading.Thread(
        target=thread_estatisticas,
        daemon=True
    )

    estatisticas.start()

    print("[GATEWAY] Aguardando mensagens dos sensores...")

    try:
        client.loop_forever()
    except:
        print('\n[*]Smart Gateway finalizado pelo operador.')
