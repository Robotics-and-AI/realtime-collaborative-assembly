import multiprocessing as mp
from camera import camera_loop
from model import model_worker
from robot import robot_loop
import logging


# define logging file for the controller process
logger = logging.getLogger("controller")
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(name)s] %(message)s')
file_handler = logging.FileHandler("controller.log")
formatter = logging.Formatter('[%(asctime)s] [%(name)s] %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def start_system(stop_event, model_ready_event, robot_online_event):
    # initialize queues and moving flag
    logger.info("Initializing processes...")
    frame_queue = mp.Queue(maxsize=20)
    result_queue = mp.Queue()
    moving_flag = mp.Value("b", False)

    # start processes
    camera_proc = mp.Process(target=camera_loop, args=(frame_queue, stop_event))
    model_proc = mp.Process(target=model_worker, args=(frame_queue, result_queue, stop_event, model_ready_event, moving_flag))
    robot_proc = mp.Process(target=robot_loop, args=(result_queue, stop_event, robot_online_event, moving_flag))

    camera_proc.start()
    model_proc.start()
    robot_proc.start()

    # log information of system readiness
    logger.info("Waiting for model to become ready...")
    if model_ready_event.wait(timeout=10):
        logger.info("System is ready")
    else:
        logger.warning("Timeout waiting for system readiness")

    robot_proc.join()
    model_proc.join()
    camera_proc.join()