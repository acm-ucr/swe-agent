import zmq
import json
import threading

def start_handshake_server(context, port):
    socket = context.socket(zmq.REP)
    socket.bind(f"tcp://*:{port}")
    print(f"[Receiver] Handshake server listening on port {port}...")

    try:
        message = socket.recv_string()
        if message == "handshake":
            print("[Receiver] Received handshake")
            socket.send_string("ack")
    finally:
        socket.close()

def text_listener(context, publisher_ip):
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://{publisher_ip}:5555")

    socket.setsockopt_string(zmq.SUBSCRIBE, "default")

    print(f"[Receiver] Listening for text messages...")

    try:
        while True:
            message = socket.recv_string()
            topic, content = message.split(" ", 1)
            print(f"[Receiver] Received text: {content} (Topic: {topic})")
    except KeyboardInterrupt:
        print("Shutting down receiver...")
        socket.close()
        context.term()

if __name__ == "__main__":
    with open("orchestrator/ip.json") as f:
        config = json.load(f)

    receiver = config["devices"]["receiver"]
    sender_ip = config["devices"]["sender"]["ip"]
    context = zmq.Context()

    threading.Thread(
        target=start_handshake_server,
        args=(context, receiver["handshake_port"]),
        daemon=True
    ).start()

    text_listener(context, sender_ip)
