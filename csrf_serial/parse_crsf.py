import binascii
import math
import string

CRSF_MAX_PAYLOAD_LEN = 62

CRSF_MODULE_ADDRESS = b'\xee'
CRSF_RADIO_ADDRESS = b'\xea'
CRSF_UART_SYNC = b'\xc8'

# Sensor Types

# Telemetry Battery stats
CRSF_SENSOR_BATTERY_TYPE = 8
CRSF_SENSOR_BATTERY_PACKET_LEN = 8

# Telemetry Flight Mode
# CRSF_SENSOR_FLIGHT_MODE = b'\x21'
CRSF_SENSOR_FLIGHT_MODE = 33
CRSF_SENSOR_MIN_FLIGHT_MODE_PACKET_LEN = 4
# Telemetry GPS
# CRSF_SENSOR_GPS_TYPE = b'\x02'
CRSF_SENSOR_GPS_TYPE = 2
CRSF_SENSOR_GPS_PACKET_LEN = 16

# Telemetry Vario
# CRSF_SENSOR_VARIO_TYPE = b'\x07'
CRSF_SENSOR_VARIO_TYPE = 7
CRSF_SENSOR_VARIO_PACKET_LEN = 3

# Telemetry Attitude
# CRSF_SENSOR_ATTITUDE_TYPE = b'\x1e'
CRSF_SENSOR_ATTITUDE_TYPE = 30
CRSF_SENSOR_ATTITUDE_PACKET_LEN = 6

# Telemetry Radio Sync Updates
CRSF_SENSOR_RADIO_TYPE = 58
CSRF_SENSOR_RADIO_PACKET_LEN = 11

# Telemetry Link Stats
CRSF_SENSOR_LINK_STAT_TYPE = 20
CSRF_SENSOR_LINK_STAT_PACKET_LEN = 10
MAX_RSSI = -30
MIN_RSSI = -120
TX_POWER = [0, 10, 25, 100, 500, 1000, 2000, 250, 50]

VERBOSE = 0

def decode_battery_stat(data):
    voltage = int.from_bytes(data[0:2], 'big')/10
    current = int.from_bytes(data[2:4], 'big')/10
    remaining_current = int.from_bytes(data[4:6], 'big')
    remaining_percentage = int.from_bytes(data[7:], 'big')
    if VERBOSE == 1:
        print('B', end='')
    elif VERBOSE > 1:    
        print(f"Battery: voltage {voltage} - current {current} - mAH remaining {remaining_current} - batt remaining {remaining_percentage}")

def decode_link_stat(data):
    txRSSI1 = -1 * data[0]
    txRSSI2 = -1 * data[1]
    txLQ = data[2]
    txSNR = data[3]
    txAntenna = data[4]
    rfMode = data[5]
    txPwr = data[6]
    txPwr = TX_POWER[txPwr] if txPwr < len(TX_POWER) else txPwr
    rxRSSI = -1 * data[7]
    rxLQ = data[8]
    rxSNR = data[9]
    rssi = txRSSI2 if txAntenna == 1 else txRSSI1
    if VERBOSE == 1:
        print('L', end='')
    elif VERBOSE > 1:
        print(f"Link Stats")
        print(f"\tLink: TX RSSI1: {txRSSI1} - TX RSSI2: {txRSSI2} - TX Antenna #: {txAntenna} - TX RSSI: {rssi}")
        print(f"\tLink: TX PWR: {txPwr} - TX LQ: {txLQ} - TX SNR: {txSNR} - RF Mode: {rfMode}")
        print(f"\tLink: RX RSSI: {rxRSSI} - RX LQ: {rxLQ} - RX SNR: {rxSNR}")    

def decode_attitude(data):
    pitch = math.degrees(float.fromhex(data[0:2].hex())/10000)
    roll = math.degrees(float.fromhex(data[2:4].hex())/10000)
    yaw = math.degrees(float.fromhex(data[4:6].hex())/10000)
    if VERBOSE == 1:
        print('A', end='')
    elif VERBOSE > 1:
        print(f"Attitude: pitch {pitch:.2f} - roll {roll:.2f} - yaw {yaw:.2f}")

def decode_radio(data):
    # Look for sync type
    if data[0:1] == b'\xea' and data[2:3] == b'\x10':
        rate = int.from_bytes(data[3:7], byteorder='big') // 10
        lag = int.from_bytes(data[7:11], byteorder='big') // 10
        if VERBOSE == 1:
            print('R', end='')
        elif VERBOSE > 1:
            print(f"Radio: rate {rate}μs - lag {lag}μs")

def decode_flightmode(data):
    if VERBOSE == 1:
        print('F', end='')
    elif VERBOSE > 1:
        fm = ''.join(filter(lambda x: x in string.printable, data.decode('ascii', errors='ignore')))
        print(f"Flight Mode: {fm:s}")

def process_payload(payload):
    sensor_type = payload[0]
    if VERBOSE > 2:
        print(f"Payload: {binascii.hexlify(payload[1:-1])}")
    if sensor_type == CRSF_SENSOR_RADIO_TYPE:
        if len(payload[1:-1]) == CSRF_SENSOR_RADIO_PACKET_LEN:
            decode_radio(payload[1:-1])
    elif sensor_type == CRSF_SENSOR_GPS_TYPE:
        if VERBOSE == 1:
            print('G', end='')
        elif VERBOSE > 1:        
            print(f"Sensor: GPS - {sensor_type:x}")
    elif sensor_type == CRSF_SENSOR_VARIO_TYPE:
        if VERBOSE == 1:
            print('V', end='')
        elif VERBOSE > 1:
            print(f"Sensor: Vario - {sensor_type:x}")
    elif sensor_type == CRSF_SENSOR_BATTERY_TYPE:
        if len(payload[1:-1]) == CRSF_SENSOR_BATTERY_PACKET_LEN:
            decode_battery_stat(payload[1:-1])
    elif sensor_type == CRSF_SENSOR_LINK_STAT_TYPE:
        if len(payload[1:-1]) == CSRF_SENSOR_LINK_STAT_PACKET_LEN:
            decode_link_stat(payload[1:-1])
    elif sensor_type == CRSF_SENSOR_ATTITUDE_TYPE:
        if len(payload[1:-1]) == CRSF_SENSOR_ATTITUDE_PACKET_LEN:
            decode_attitude(payload[1:-1])
    elif sensor_type == CRSF_SENSOR_FLIGHT_MODE:
        decode_flightmode(payload[1:-1])
    else:
        if VERBOSE == 1:
            print('U', end='')
        elif VERBOSE > 1:
            print(f"Sensor: Unknown {sensor_type:x}")
  
def read_stream(input_stream, output_stream):
        frame = bytearray()
        while first_byte := input_stream.read(1):
            if output_stream:
                output_stream.write(first_byte)
            if first_byte == CRSF_RADIO_ADDRESS:
                len_byte = input_stream.read(1)
                if output_stream:
                    output_stream.write(len_byte)
                if len_byte == None:
                    return
                if int.from_bytes(len_byte, 'big') <= CRSF_MAX_PAYLOAD_LEN:
                    payload = input_stream.read(int.from_bytes(len_byte, 'big'))
                    if output_stream:
                        output_stream.write(payload)
                    # TODO: Implement CRC Check
                    crc_byte = payload[-1]
                    process_payload(payload)
                else:
                    if VERBOSE == 1:
                        print('.', end='')
                    elif VERBOSE > 1:
                        print(f"{len_byte:x}")
            else:
                if VERBOSE == 1:
                    print(".", end='')
                elif VERBOSE > 1:
                    print(f"{binascii.hexlify(first_byte)}")