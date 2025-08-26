import time
from pymodbus.server import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
import logging
import threading


# logging and monitoring
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

RTU_ADDRESS = 13
TCP_PORT = 502

TANK_CAPACITY = 1000
tank_level = 500  #initial fuel level

FILL_RATE = 10       # l/s
PUMP_RATES = [10,10,5] # P1,P2,P3

HIGH_ALARM = 900
LOW_ALARM = 150

#Modbus map
store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(0, [0]*10),   # digitalni ulazi, 10 ulaza -->svi nula
    co=ModbusSequentialDataBlock(2000, [0]*10), # coils = pumpe i ventil, 2000 predstavlja ventil1 npr->startna adresa
    #ovo se mora mnoziti sa 10 zbog EGU_value = A * raw_value + B --> 2 dana dok sam otkrila bag
    #coils: V1, P1, P2, P3
    hr=ModbusSequentialDataBlock(1000, [tank_level]*10), # analogni izlazi = nivo goriva, trenutni nibo
    ir=ModbusSequentialDataBlock(0, [0]*10),   # input registers, read-only registri (master može samo da čita)
    unit=RTU_ADDRESS #adresa slave uredjaja, da se zna sa kojim se uredjajem komunicira
)

context = ModbusServerContext(slaves=store, single=True)

identity = ModbusDeviceIdentification()
identity.VendorName = 'SCADA'
identity.ProductCode = 'BP'
identity.VendorUrl = 'http://example.com'
identity.ProductName = 'BenzinskaPumpa'
identity.ModelName = 'BP-Sim'
identity.MajorMinorRevision = '1.0'

def main_function():
    global tank_level
    while True:
        co = context[0].getValues(1, 2000, count=4) #1 oznacava coils, 2discrete inputs, 3 ir, 4hr
        #2000 startna adresa, count=4, 4 uzastopna 2000 = V1,2001 = P1,2002 = P3,2003 = P3
        V1 = co[0]
        pumps = co[1:4] #P1 = co[1] P2 = co[2] P3 = co[3]

        #tekst iz zadatka:  Zabraniti otvaranje ventila dok pumpe rade, znaci zabranjeno punjenje dok pumpe rade
        if V1 and any(pumps): 
            log.warning("Abnormal alarm: valve is open while pumps are running!") 
            context[0].setValues(1, 2000, [0])
            V1 = 0

        #tekst iz zadatka: zabraniti uključivanje pumpi dok je ventil otvoren, znaci bilo koja pumpa ako je ukljucena gasi se ako je V ukljucen
        for i, pump in enumerate(pumps):
            if pump and V1:
                log.warning("Abnormal alarm: at least one pump is ON while valve is open")
                context[0].setValues(1, 2000 + (i+1), [0])
                pumps[i] = 0

        if V1 and not any(pumps):
            tank_level += FILL_RATE
            if tank_level > TANK_CAPACITY:
                tank_level = TANK_CAPACITY
            log.info(f"Tank filling: {tank_level} l")

         for i, p in enumerate(pumps):
            if p and not V1:
                tank_level -= PUMP_RATES[i]
                if tank_level < 0:
                    tank_level = 0
                log.info(f"Pump P{i+1} active, tank level: {tank_level} l")

        context[0].setValues(3, 1000, [tank_level])

        if tank_level > HIGH_ALARM:
            log.warning("High alarm! Tank level above 900 l")
        elif tank_level < LOW_ALARM:
            log.warning("Low alarm! Tank level below 150 l")

        time.sleep(1)

def run_server():
    StartTcpServer(
        context=context,
        identity=identity,
        address=("0.0.0.0", TCP_PORT)
    )

if __name__ == "__main__":
    threading.Thread(target=main_function, daemon=True).start()
    run_server()

