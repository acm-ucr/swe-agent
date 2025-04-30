import zmq
import json
import time

def main():
    
    with open("orchestrator/ip.json") as f:
        config = json.load(f)

    receiver = config["devices"]["receiver"]
    context = zmq.Context()

    print("Attempting handshake...")
    socket = context.socket(zmq.REQ)
    socket.connect(f"tcp://{receiver['ip']}:{receiver['handshake_port']}")
    
    socket.send_string("handshake")
    try:
        response = socket.recv_string(flags=zmq.NOBLOCK)
        if response == "ack":
            print("Handshake successful. Proceed with publishing.")
        else:
            print(f"Unexpected response: {response}")
    except zmq.Again:
        print("Handshake timed out. Exiting.")
    
    socket.close()
    context.term()

if __name__ == "__main__":
    main()
