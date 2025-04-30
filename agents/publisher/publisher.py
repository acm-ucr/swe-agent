import zmq
import json
import time

def publish_text(context, receiver_ip, port, message):
    socket = context.socket(zmq.PUB)
    socket.connect(f"tcp://{receiver_ip}:{port}")

    for _ in range(5):
        socket.send_string(f"default {message}")  # apparently i need topics? tf? i will use default
        print(f"Sent: {message}")
        time.sleep(1)

    socket.close()

if __name__ == "__main__":
    with open("orchestrator/ip.json") as f:
        config = json.load(f)

    receiver = config["devices"]["receiver"]
    context = zmq.Context()

    publish_text(context, receiver["ip"], receiver["port"], "what if i wasnt the skibidi rizzler")
