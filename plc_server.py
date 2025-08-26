from pymodbus.server import StartTcpServer
from pymodbus.device import ModbusDeviceIdentification
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext, ModbusSequentialDataBlock
import logging


# logging and monitoring
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)

RTU_ADDRESS = 13
TCP_PORT = 502

TANK_CAPACITY = 1000
tank_level = 500  #initial fuel level

#Modbus map
store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(0, [0]*10),   # digitalni ulazi, 10 ulaza -->svi nula
    co=ModbusSequentialDataBlock(2000, [0]*10), # coils = pumpe i ventil, 2000 predstavlja ventil1 npr->startna adresa
    #ovo se mora mnoziti sa 10 zbog EGU_value = A * raw_value + B --> 2 dana dok sam otkrila bag
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

def run_server():
    StartTcpServer(
        context=context,
        identity=identity,
        address=("0.0.0.0", TCP_PORT)
    )

if __name__ == "__main__":
    run_server()
