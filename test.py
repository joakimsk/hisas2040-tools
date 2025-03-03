import socket

# Create a UDP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Bind the socket to the address and port
server_address = ('', 8010)  # '' makes it listen on all available interfaces
sock.bind(server_address)

print("Listening for UDP packets on port 8010...")

try:
    while True:
        # Receive data
        data, address = sock.recvfrom(4096)  # Buffer size is 4096 bytes
        print(f"Received {len(data)} bytes from {address}")
        print(f"Data: {data.decode('utf-8', errors='ignore')}")  # Assuming text data
except KeyboardInterrupt:
    print("Server stopped.")
finally:
    sock.close()
