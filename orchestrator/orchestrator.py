import zmq
import json
import time

def main():
    topics = ["Topic"]
    with open("ip.json") as f:
        config = json.load(f)
    
    receiver = config["devices"]["receiver"]
    context = zmq.Context()

    print("Attempting handshake...")
    socket = context.socket(zmq.PUB)
    socket.bind(f"tcp://*:5555")
    
    try:
        start_time = time.time()
        duration = 10
        while time.time() - start_time < duration:
            for i , topic in enumerate(topics):
                socket.send_string(f"{topic} [`i am the rizzler`]")
                time.sleep(2)
    except zmq.Again:
        print("Handshake timed out. Exiting.")
    
    socket.close()
    context.term()

if __name__ == "__main__":
    main()
