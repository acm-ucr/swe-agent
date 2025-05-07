import zmq
import json
import time

def publish_text(context, receiver_ip, port, topics, message):
    socket = context.socket(zmq.PUB)
    socket.connect(f"tcp://{receiver_ip}:{port}")

    for _ in range(5):
        for i, topic in enumerate(topics):
            print(f"Sent: {topic} {message}")  # apparently i need topics? tf? i will use default
        time.sleep(1)

    socket.close()

if __name__ == "__main__":
    with open("orchestrator/ip.json") as f:
        config = json.load(f)

    receiver = config["devices"]["receiver"]
    context = zmq.Context()

    publish_text(context, receiver["ip"], receiver["port"], {"Topic"}, "what if i wasnt the skibidi rizzler")
