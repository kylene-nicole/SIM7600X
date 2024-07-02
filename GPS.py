#!/usr/bin/python

import Jetson.GPIO as GPIO
import serial
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

ser = serial.Serial('/dev/ttyTHS1', 115200)
ser.flushInput()

power_key = 6
rec_buff = ''
rec_buff2 = ''
time_count = 0

def send_at(command, back, timeout):
    rec_buff = ''
    ser.write((command + '\r\n').encode())
    time.sleep(timeout)
    if ser.inWaiting():
        time.sleep(0.01)
        rec_buff = ser.read(ser.inWaiting())
    if rec_buff != '':
        if back not in rec_buff.decode():
            logging.error(f'{command} ERROR')
            logging.error(f'{command} back:\t{rec_buff.decode()}')
            return 0
        else:
            logging.info(rec_buff.decode())
            return 1
    else:
        logging.warning('GPS is not ready')
        return 0

def get_gps_position():
    rec_null = True
    answer = 0
    logging.info('Start GPS session...')
    send_at('AT+CGPS=1,1', 'OK', 1)
    time.sleep(2)
    while rec_null:
        answer = send_at('AT+CGPSINFO', '+CGPSINFO: ', 1)
        if 1 == answer:
            if ',,,,,,' in rec_buff:
                logging.info('GPS is not ready')
                rec_null = False
                time.sleep(1)
            else:
                logging.info('GPS data received')
                rec_null = False
        else:
            logging.error(f'Error {answer}')
            send_at('AT+CGPS=0', 'OK', 1)
            return False
        time.sleep(1.5)
    # Clean up data if necessary
    send_at('AT+CGPS=0', 'OK', 1)
    return True

def power_on(power_key):
    logging.info('SIM7600X is starting...')
    GPIO.setmode(GPIO.BCM)
    GPIO.setwarnings(False)
    GPIO.setup(power_key, GPIO.OUT)
    time.sleep(0.1)
    GPIO.output(power_key, GPIO.HIGH)
    time.sleep(2)
    GPIO.output(power_key, GPIO.LOW)
    time.sleep(20)
    ser.flushInput()
    logging.info('SIM7600X is ready')

def power_down(power_key):
    logging.info('SIM7600X is logging off...')
    GPIO.output(power_key, GPIO.HIGH)
    time.sleep(3)
    GPIO.output(power_key, GPIO.LOW)
    time.sleep(18)
    logging.info('Goodbye')

def main():
    try:
        power_on(power_key)
        if get_gps_position():
            logging.info('GPS position obtained successfully')
        else:
            logging.error('Failed to obtain GPS position')
        power_down(power_key)
    except Exception as e:
        logging.error(f'Exception occurred: {e}')
        if ser is not None:
            ser.close()
        power_down(power_key)
        GPIO.cleanup()
    finally:
        if ser is not None:
            ser.close()
        GPIO.cleanup()

if __name__ == '__main__':
    main()
