import socket

class RobotController:
    def __init__(self, ip, port = 5000):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.ip = ip
        self.port = port
        self.connected = False
    
    def connect(self):
        try:
            self.client.connect((self.ip, self.port))
            self.connected = True
            print("Connected!")
        except Exception as e:
            print("Connect Failed:", e)
    
    def send_command(self, cmd):
        if self.connected:
            try:
                self.client.sendall(cmd.encode())
            except:
                self.connected = False

    def close(self):
        self.client.close()