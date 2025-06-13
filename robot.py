import time
import logging
import os
from robot_setup.task_data import TaskData
from robot_setup.robot_communication import RobotCommunication
from robot_setup.robotic_system import RoboticSystem
from settings import constants


# define logging file for the robot process
logger = logging.getLogger("robot")
logging.basicConfig(level=logging.DEBUG if constants.DEBUG else logging.INFO, format='[%(asctime)s] [%(name)s] %(message)s')
file_handler = logging.FileHandler("robot.log")
formatter = logging.Formatter('[%(asctime)s] [%(name)s] %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def robot_loop(result_queue, stop_event, robot_online_event, moving_flag):
    def load_tasks(robotic_system: RoboticSystem, tasks: list):
        """
        Load tasks executed by the robot.
        :param robotic_system: robot system where tasks are loaded
        :param tasks: list of task labels
        """
        try:
            for task in tasks:
                if not robotic_system.exists_task(task):
                    robotic_system.load_task(task)
        except Exception:
            raise

    # setup robotic system
    logger.info("Initializing robot objects")
    task_data = TaskData(os.path.join(os.path.abspath(""), "robot_setup", "sub_assemblies"))
    robot_communication = RobotCommunication(os.path.join(os.path.abspath(""), "robot_setup", "tools.json"))
    robotic_system = RoboticSystem(robot_communication, task_data)

    logger.info("Starting robot connection")

    # start robot connection
    try:
        robotic_system.start_robot_connection("172.31.1.147")
    except Exception as e:
        logger.error("Robot failed to connect", exc_info=True)
        return

    logger.info("Robot connected")

    # inform robot is ready
    robot_online_event.set()
    last_heartbeat = time.time()

    robot_tasks_count = 0
    robot_tasks_remaining = {}

    # get task labels and load them
    try:
        for label in constants.EXPECTED_TASKS:
            robot_tasks_count += len(constants.ROBOT_TASK_TIME[label])
            if len(constants.ROBOT_TASK_TIME[label]) == 1:
                robot_tasks_remaining[constants.EXPECTED_TASKS[label]] = [label]
            else:
                robot_tasks_remaining[constants.EXPECTED_TASKS[label]] = \
                    [f"{label}{i}" for i in range(len(constants.ROBOT_TASK_TIME[label]), 0, -1)]
            load_tasks(robotic_system, robot_tasks_remaining[constants.EXPECTED_TASKS[label]])
    except Exception as e:
        logger.error("Failed to load task", exc_info=True)
        robotic_system.stop_robot_connection()
        logger.info("Robot connection closed")
        return

    try:
        while not stop_event.is_set():
            if not result_queue.empty():
                # get predicted sub-assembly
                task_class = result_queue.get()
                logger.info(f"Sub-assembly: {task_class}")

                # if there are not remaining tasks in classified sub-assembly inform failure and shut down
                if len(robot_tasks_remaining[task_class]) == 0:
                    logger.warning(f"No more remaining tasks with label {task_class}")
                    logger.info("Closing robot connection, and triggering system shutdown")
                    stop_event.set()
                    break
                
                # safeguard to prevent the robot from doing a task different to W_1 after doing task W_0
                if len(robot_tasks_remaining[5]) == 1 and task_class != 5:
                    logger.warning(f"Drop wheel task failed! Task selected {task_class}! Shutting system down")
                    break

                # execute classified task
                logger.info("Starting robot movement")
                robotic_system.run_task(robot_tasks_remaining[task_class].pop())
                logger.info("Robot movement stopped")
                moving_flag.value = False

            if time.time() - last_heartbeat > 5:
                logger.info("Robot still running...")
                last_heartbeat = time.time()

            time.sleep(0.01)

    except Exception as e:
        logger.error("Robot crashed", exc_info=True)

    finally:
        if robotic_system.is_robot_connected():
            robotic_system.stop_robot_connection()
        logger.info("Robot stopping")
