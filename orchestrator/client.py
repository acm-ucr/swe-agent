import zmq
import json
import threading
import time

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

def text_listener(context, publisher_ip, inactivity_timeout=10):
    socket = context.socket(zmq.SUB)
    socket.connect(f"tcp://{publisher_ip}:5555")
    socket.setsockopt_string(zmq.SUBSCRIBE, "default")
    print(f"[Receiver] Listening for text messages...")

    last_received = time.time()
    contents = []

    try:
        while True:
            if socket.poll(timeout=1000):  # Timeout is in milliseconds
                try: 
                    message = socket.recv_string()
                except zmq.error.ZMQError:
                    break
                topic, content = message.split(" ", 1)
                print(f"[Receiver] Received text: {content} (Topic: {topic})")
                last_received = time.time()
                contents.append(content)
            else:
                if time.time() - last_received > inactivity_timeout:
                    print(f"No messages received for {inactivity_timeout} seconds. Shutting down receiver...")
                    break
    except KeyboardInterrupt:
        print("Shutting down receiver (keyboard interrupt)...")
    finally:
        try:
            socket.close()
        except Exception:
            pass
    
    return contents

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
