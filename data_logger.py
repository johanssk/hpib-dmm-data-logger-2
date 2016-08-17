
__version__ = 4
import os.path
import sys
import time
import datetime
import serial
import logging
import tqdm
import csv
# from data_logger_configuration import *
# from data_logger_configuration import COM_PORT
from data_logger_configuration import OUTPUT_SAVE_PATH
from data_logger_configuration import OUTPUT_SAVE_NAME
from data_logger_configuration import SEND_CMD
from data_logger_configuration import SAMPLE_TIME
from data_logger_configuration import OUTPUT_SAVE_EXTENTION
from data_logger_configuration import TIME_SLEEP_READ
from data_logger_configuration import SETUP_CMD

logging.basicConfig(level=logging.DEBUG, format=' %(asctime)s - %(levelname)s- %(message)s')
logging.disable(logging.DEBUG)

class TimeError(Exception):
    pass
class PathError(Exception):
    pass

def read_write(my_ser):
    """
    Sets up device and sends commands, then reads response

    INPUT 
    my_ser = serial connection

    OUTPUT 
    out: List of tuples of format (time_of_reading, reading)
    """
    try:
        # Assigns variables from configuration file to local variables
        # Used to speed up while loop
        setup = SETUP_CMD
        send = SEND_CMD
        sleep_read = TIME_SLEEP_READ
        sample = SAMPLE_TIME

        logging.debug("Setup command: %s" % setup)
        logging.debug("Send command: %s" % send)
        logging.debug("Time sleep read: %s" % sleep_read)
        logging.debug("Sample time: %s" % sample)

        logging.info("Inputting device settings")
        my_ser.write("%s\n" % setup)

        # Initialize list to contain readings
        out = []

        # Assign function lookups to variables
        # Used to speed up while loop
        current_time = time.time
        write = my_ser.write
        read = my_ser.read
        rstrip = str.rstrip
        sleep = time.sleep
        append = out.append

        logging.info("Beginning data logging")

        while True:
            start_time = current_time()

            logging.debug("Sending command: %s" % send)
            write("%s\n" % send)

            sleep(sleep_read)

            return_string = rstrip(str(read(256)))
            append((current_time(), return_string))

            if len(return_string) > 0:
                print return_string
            else:
                logging.critical("No response from system")
                return False
            
            offset = current_time() - start_time
            logging.debug("Offset: %f", offset)
            if sample - offset > 0:
                sleep(sample - offset)
            print current_time() - start_time
    except KeyboardInterrupt:
        logging.info("Done logging")
        return out

def write_file(out, output_save_path, output_save_name, output_save_extention):
    """
    Writes data to specified file

    INPUT 
    out: List of tuples of format (time_of_reading, reading)

    OUTPUT 
    File at location LOG_SAVE_PATH, with filename of format
    "LOG_SAVE_NAME %Y-%m-%d %H_%M_%S" and extension LOG_SAVE_EXTENTION
    """
    logging.info("Saving values to file")
    now = datetime.datetime.now()
    file_time = now.strftime("%Y-%m-%d %H_%M_%S")

    filename = "%s %s%s" % (output_save_name, file_time, output_save_extention)
    logging.debug(filename)

    full_filename = os.path.join(output_save_path, filename)
    logging.info("Saving as: %s", full_filename)

    with open(full_filename, 'a+') as data:
        for pair in tqdm.tqdm(out):
            write_line = "%s,%s\n" % (str(pair[0]), str(pair[1]))
            data.write(write_line)
    return full_filename

def auto_connect_device():
    """
    Runs through COM 0-4 and connects to correct device

    INPUT 
    None

    OUTPUT 
    try_ser if connected and device responding
    boolean False if no connection
    """
    logging.info("Connecting to device")
    for com_port in xrange(5):
        logging.debug("Trying COM%i" % com_port)
        try:
            # try_ser = serial.Serial('\\\\.\\COM' + str(com_port), 9600, timeout=0.5)
            try_ser = serial.Serial('COM' + str(com_port), 9600, timeout=0.5)
            try_ser.write("%s\n" % SEND_CMD)
            time.sleep(TIME_SLEEP_READ)
            test_read = try_ser.read(256).strip()
            logging.debug(test_read)
            logging.debug("Length test_read: %i" % len(test_read))
            if not len(test_read) > 0:
                continue
            logging.info("Connected to COM%i" % com_port)
            return try_ser
        except WindowsError:
            continue
        except serial.SerialException:
            continue
    logging.critical("Error connecting to device")
    return False

if __name__ == '__main__':
    start_total_time = time.time()
    ser = serial.Serial()
    
    try:
        # assert SAMPLE_TIME > 0
        if not SAMPLE_TIME > 0:
            raise TimeError
        if not TIME_SLEEP_READ > 0:
            raise TimeError
        # assert TIME_SLEEP_READ > 0
        if not os.path.isdir(OUTPUT_SAVE_PATH):
            raise PathError
        # assert os.path.isdir(LOG_SAVE_PATH)
        
        ser = auto_connect_device()
        if not ser:
            sys.exit()
        output = read_write(ser)
        if output != False:
            write_file(output, OUTPUT_SAVE_PATH, OUTPUT_SAVE_NAME, OUTPUT_SAVE_EXTENTION)
            ser.close()
        print "Total Time: %s" % (time.time()-start_total_time)

    except serial.SerialException, e:
        logging.critical(e)

    except KeyboardInterrupt, e:
        ser.close()
        logging.critical(e)
    except WindowsError, e:
        logging.critical("Cannot open port specified")
        print "Error in configuration file"
    except TimeError:
        logging.critical("SAMPLE_TIME and TIME_SLEEP_READ must be greater than zero. Fix in configuration file.")
        print "Error in configuration file"
        # print("SAMPLE_TIME and TIME_SLEEP_READ must be greater than zero")
    except PathError:
        logging.critical("Invalid save path. Fix in configuration file.")
        print "Error in configuration file"
    # except AssertionError, e:
    #     print e
    #     print "Fix errors in configuration file"
    #     logging.error("Fix errors in configuration file")