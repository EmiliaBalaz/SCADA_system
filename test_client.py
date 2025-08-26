from pymodbus.client import ModbusTcpClient
import time

TCP_IP = "127.0.0.1"
TCP_PORT = 502

client = ModbusTcpClient(TCP_IP, port=TCP_PORT)
client.connect()

def read_tank():
    rr = client.read_holding_registers(1000, 1, unit=13)
    if rr.isError():
        print("Error reading tank level")
        return None
    return rr.registers[0]

def read_coils():
    rr = client.read_coils(2000, 4, unit=13)
    if rr.isError():
        print("Error reading coils")
        return None
    return rr.bits

def write_coil(address, value):
    client.write_coil(address, value, unit=13)

try:
    while True:
        print("\n--- Current State ---")
        print("Tank level:", read_tank())
        print("Coils (V1, P1, P2, P3):", read_coils())
        
        cmd = input("Command (V1/P1/P2/P3 on/off or q to quit): ").strip().lower()
        if cmd == "q":
            break
        elif cmd in ["v1 on", "v1 off", "p1 on", "p1 off", "p2 on", "p2 off", "p3 on", "p3 off"]:
            coil_map = {"v1":2000, "p1":2001, "p2":2002, "p3":2003}
            name, action = cmd.split()
            write_coil(coil_map[name], 1 if action=="on" else 0)
        else:
            print("Invalid command")
        
        time.sleep(0.5)

finally:
    client.close()
