import serial
import time
import multiprocessing
from pymodbus.client.sync import ModbusTcpClient
from pymodbus.payload import BinaryPayloadDecoder
from pymodbus.constants import Endian


class PCCU_Process(multiprocessing.Process):
    def __init__(self, q_serial, q_readings, q_ctrl, q_web_ctrl, q_tflow_inch_readings, q_tflow_psi_readings):
        multiprocessing.Process.__init__(self)
        self.q_serial = q_serial
        self.q_readings = q_readings
        self.q_ctrl = q_ctrl
        self.q_web_ctrl = q_web_ctrl
        self.q_readings = q_readings
        self.q_tflow_inch_readings = q_tflow_inch_readings
        self.q_tflow_psi_readings = q_tflow_psi_readings

        self.tflow_num_reg = 6 # number of modbus register to read in
        self.tflow_start_reg = 7000 # starting register
        self.num_reg # number of registers to read in
        self.tflow_TCP_address = '192.168.88.90'
        self.tflow_TCP_port = '502'
        self.tflow_TCP_unit = '1'
        self.tflow_connect = 0

        self.prev_msg = ""

        try:
            client = ModbusTcpClient(self.tflow_TCP_address, port=self.TCtflow_TCP_port)
            client.connect()
        except:
            print("Not able to connect to totalflow tcp")
        else:
            print("TCP to totalflow open")
            self.good_tflow_connect = 1

    def close(self):
        try:
            client.close()
        except:
            print("Not able to close the tcp connection to totalflow")

    def write_tflow(self, data):
        pass

    def read_tflow(self):
        result = client.read_holding_registers(self.tflow_start_reg, self.tflow_num_reg, unit=self.tflow_TCP_unit) # register start, number of registers, unit id
        decoder = BinaryPayloadDecoder.fromRegisters(result.registers, byteorder=Endian.Big, wordorder=Endian.Little)

        reg_arr = []
        for i in range(0,int(num_reg / 2)):

    def cprint(self, msg):
        if msg != self.prev_msg:
            print(msg)
            self.prev_msg = msg

    def run(self):
        print("tflow_data.py running")

        while True:
            #print("True")
            # look for incoming tornado request
            if not self.q_pccu.empty():
                data = self.q_pccu.get()

                # send it to the serial device
                self.write_pccu(data)
                #print("writing to serial: " + data)

            # look for incoming serial data
            try:
                inw = self.ser.in_waiting
            except:
                self.poll_fail_msg()
                print("problem with in_waiting")
                try:
                    self.ser.close()
                    print("Serial port closed")
                except:
                    print("Not able to close the serial port instance")
                i = 5
                while i > 0:
                    print("(run) Attempting to re-open serial port in %s" %i)
                    i -= 1
                    time.sleep(1)
                try:
                   self.ser = serial.Serial(SERIAL_PORT, SERIAL_BAUDRATE, timeout=1, parity=serial.PARITY_NONE, rtscts=0)
                except:
                    print("Not able to start new instance of serial port")
                else:
                    print("Serial port re-opened")
            else:
                if (inw > 0):
                    #print("inw")
                    data = self.readSerial()
                    #print(data)
                    self.q_readings.put(data)
                    #while not self.q_data_inch.empty():
                    #    var = self.q_data_inch.get()
                    while not self.q_pccu_inch_readings.empty():
                        var = self.q_pccu_inch_readings.get()
                    self.q_pccu_inch_readings.put(data)
                    self.q_pccu_psi_readings.put(data)
                    #print(type(data['in_num']))

