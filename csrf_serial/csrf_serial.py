import cereal, parse_crsf
import serial
import signal
import argparse
from pathlib import Path

IN_STREAM = None
OUT_STREAM = None

def clean_exit():
    if IN_STREAM:
        IN_STREAM.close()
    if OUT_STREAM:
        OUT_STREAM.close()

def signal_handler(signum, frame):
    clean_exit()
    exit(0)

if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal_handler)
    parser = argparse.ArgumentParser(
                        prog = 'csrf_serial',
                        description = 'Process CSRF Telemetry Data',
                        epilog = 'NOTE: Requires Telemetry Mirror to be enabled in OpenTX/EdgeTX and exposed on USB/Serial port')
    parser.add_argument('--serial_idx', type=int, default=None, help='Index number for the serial ports')
    parser.add_argument('--input_file', type=Path, help='Filename to read telemetry from (Ignores serial port)')
    parser.add_argument('--output_file', type=Path, help='Filename to capture telemetry to')
    parser.add_argument('--verbose', type=int, default=0, help="Verbose value, default is 0 (print nothing), 1 prints received packet type, 2 prints ascii payload, 3 prints hex output")
    
    args = None
    try:
        args = parser.parse_args()
    except Exception as e:
        parser.print_help()
        parser.exit(status=1, message=f'ERROR: {e}')
    parse_crsf.VERBOSE = args.verbose
 
    if args.input_file == None: 
        if args.serial_idx != None:
            port_list = cereal.serial_ports()
            if args.serial_idx < len(port_list):
                IN_STREAM = serial.Serial(port_list[args.serial_idx])
            else:
                parser.print_help()
                parser.exit(status=1, message=f'Invalid Serial port index: {args.serial_idx}\n')
        else:
            IN_STREAM = serial.Serial(cereal.select_port())
        if args.output_file:
            try:
                OUT_STREAM = open(args.output_file, 'wb')
            except Exception as e:
                parser.print_help();
                clean_exit()
                parser.exit(status=1, message=f'{e}')
        print("Processing packets, press CTRL-C to stop processing")
    else:
        try:
            IN_STREAM = open(args.input_file,'rb')
        except Exception as e:
                parser.print_help();
                clean_exit()
                parser.exit(status=1, message=f'{e}')            
    # Process Packets
    parse_crsf.read_stream(IN_STREAM, OUT_STREAM)
                  