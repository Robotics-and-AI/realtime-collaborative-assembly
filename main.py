import serial
from serial import SerialException
from serial.tools import list_ports
import multiprocessing as mp
import time
import logging
from settings import constants
from controller import start_system

def find_port():
    """
    Search the Arduino board and return its COM port.
    :return: COM port of the Arduino board
    """
    # get ports and find if any one matches with the Arduino board type
    ports = list_ports.comports()
    com_port = None
    for port, desc, hwid in ports:
        if constants.ARDUINO_BOARD in desc:
            com_port = port

    # raise IOError if the board was not found
    if com_port is None:
        raise IOError(f"Board {constants.ARDUINO_BOARD} was not found!")
    return com_port

def send_buzz(ser, freq, duration):
    """
    Send command to the Arduino board to buzz with a specific frequency for a certain duration.
    :param ser: serial connection with the Arduino board
    :param freq: frequency of the sound [Hz]
    :param duration: duration of the sound [ms]
    """
    ser.write(f"buzz_{freq}_{duration}\n".encode())
    # wait the sound duration plus a small margin
    time.sleep((duration / 1000.0) + 0.05)

# define logging file for the main process
logger = logging.getLogger("main")
logging.basicConfig(level=logging.DEBUG if constants.DEBUG else logging.INFO, format='[%(asctime)s] [%(name)s] %(message)s')
file_handler = logging.FileHandler("main.log")
formatter = logging.Formatter('[%(asctime)s] [%(name)s] %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def run_system(stop_event, model_ready_event, robot_online_event):
    start_system(stop_event, model_ready_event, robot_online_event)

def main():
    logger.info("Connecting Arduino")

    # attempt Arduino connection
    try:
        BAUDRATE = 9600
        SERIAL_PORT = find_port()
        ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)
    except Exception as e:
        logger.error("Arduino connection failed")
        return

    logger.info("Arduino connected sucessfully")

    # setup events to trigger stop and to trigger system ready buzzes
    stop_event = mp.Event()
    model_ready_event = mp.Event()
    robot_online_event = mp.Event()
    system_proc = None

    try:
        while True:
            # terminate system if stop event has been set
            if stop_event.is_set():
                system_proc.join()
                system_proc = None
                break
            
            # terminate system if Arduino connection is not open
            if not ser.is_open:
                raise SerialException("Serial connection is not open")
            
            # get button information from the Arduino board
            line = ser.readline().decode().strip()
            if line == "white" and system_proc is None:
                # start system if white button has been pressed
                logger.info("START received, starting system.")
                stop_event.clear()
                model_ready_event.clear()
                robot_online_event.clear()
                system_proc = mp.Process(target=run_system, args=(stop_event, model_ready_event, robot_online_event))
                system_proc.start()

                # wait for system ready events and buzz accordingly
                if model_ready_event.wait(timeout=10):
                    logger.info("Model ready, notifying Arduino")
                    send_buzz(ser, 300, 250)
                    send_buzz(ser, 600, 250)
                    if robot_online_event.wait(timeout=5):
                        send_buzz(ser, 900, 250)
                else:
                    logger.warning("Model failed to signal readiness in time")
    
            elif line == "red" and system_proc is not None:
                # if red button was pressed shutdown system
                logger.info("STOP received, shutting system down.")
                stop_event.set()
                system_proc.join()
                system_proc = None
                break

            elif line == "red" and system_proc is None:
                # if red button was pressed and system was not initialize terminate accordingly
                logger.info("STOP received, shutting system down.")
                break

    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received. Shutting down.")
        if system_proc:
            stop_event.set()
            system_proc.join()
    
    except Exception:
        logger.error("Connection died")
        if system_proc:
            stop_event.set()
            system_proc.join()

    finally:
        # buzz to inform system down and close serial connection
        if ser.is_open:
            send_buzz(ser, 600, 250)
            send_buzz(ser, 300, 250)
            ser.close()
        logger.info("Serial closed")

if __name__ == "__main__":
    main()
