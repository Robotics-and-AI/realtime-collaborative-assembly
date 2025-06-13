import re
import time

from robot_setup.robot_communication import RobotCommunication
from robot_setup.task_data import TaskData


class RoboticSystem:
    def __init__(self, robot: RobotCommunication, task_data: TaskData):
        self._robot = robot
        self._task_data = task_data

    def _validate_str(self, name: str) -> str:
        """
        Validate name input. Extra spaces are trimmed and final format is: Aaa aaa aaa.

        :param name: name to validate
        :return: return validated name
        """
        name = re.sub(r'[^\w_. -]', '', name)
        name = name.replace("_", " ").strip()
        if name:
            name = " ".join(name.split()).lower()
            name = name[0].upper() + name[1:]
            return name
        return ""

    def _encode_str(self, input_str: str) -> str:
        """
        Encodes name for file storage and "database" management. It follows the format: aaa_aaa_aaa.

        :param input_str: input to encode
        :return: encoded string
        """
        return input_str.lower().strip().replace(" ", "_")

    def _decode_str(self, input_str: str) -> str:
        """
        Decode name to display.

        :param input_str: input to decode
        :return: decoded input
        """
        if input_str == "":
            return input_str
        return input_str[0].upper() + input_str[1:].replace("_", " ")

    def _decode_str_list(self, encoded_str_list):
        """
        Decode list of strings.

        :param encoded_str_list: list of strings to decode
        :return: decoded list of stings
        """
        decoded_str_list = []
        for encoded_str in encoded_str_list:
            decoded_str_list.append(self._decode_str(encoded_str))
        return decoded_str_list

    def add_task(self, task_name: str) -> str:
        """
        Add new task to the "database".

        :param task_name: name of the task
        :return: validated name
        """
        task_name = self._validate_str(task_name)
        if task_name == "":
            raise ValueError(f"Name {task_name} is not valid! Make sure it has characters that are not space and "
                             f"underscore")

        encoded_name = self._encode_str(task_name)
        try:
            self._task_data.add_task(encoded_name)
        except ValueError:
            raise
        return task_name

    def load_task(self, task_name: str) -> str:
        """
        load a preexisting task to the "database".

        :param task_name: name of the task to load
        :return: validated name
        """
        task_name = self._validate_str(task_name)
        encoded_name = self._encode_str(task_name)
        try:
            self._task_data.load_task(encoded_name)
        except ValueError:
            raise
        except FileNotFoundError:
            raise
        return task_name

    def delete_task(self, task_name: str, delete_file: bool) -> None:
        """
        Delete task from "database".

        :param task_name: name of task to delete
        :param delete_file: if True delete corresponding file
        """
        encoded_name = self._encode_str(task_name)
        try:
            self._task_data.delete_task(encoded_name, delete_file)
        except ValueError:
            raise

    def save_task(self, task_name: str) -> None:
        """
        Save task into file.

        :param task_name: name of task to save
        """

        encoded_name = self._encode_str(task_name)
        try:
            self._task_data.save_task(encoded_name)
        except ValueError:
            raise

    def get_task_info(self, task_name: str) -> dict:
        """
        Get task data from name.

        :param task_name: name of the task
        :return: task's data
        """
        encoded_name = self._encode_str(task_name)
        try:
            task = self._task_data.get_task_info(encoded_name)
            task["positions"] = self._decode_str_list(task["positions"])
            for i in range(len(task["operations"])):
                task["operations"][i]["position"] = self._decode_str(task["operations"][i]["position"])
            return task
        except ValueError:
            raise

    def get_tasks(self) -> list:
        """Returns list of tasks"""
        return self._decode_str_list(self._task_data.get_tasks())

    def add_operation(self, task_name: str) -> dict:
        """
        Add a new operation to the given task

        :param task_name: name of task
        :return: created operation
        """
        encoded_name = self._encode_str(task_name)
        try:
            return self._task_data.add_operation(encoded_name)
        except ValueError:
            raise

    def update_operation(self, task_name: str, index: int, operation_type: str, position: str = "",
                         wait_input: bool = False, delay: float = 1, linear_velocity: float = 5,
                         tool: str = "") -> dict:
        """
        Update operation in the given task.

        :param task_name: name of the task
        :param index: index of the operation to update
        :param operation_type: type of operation
        :param position: position to move to (valid for "move line" tasks)
        :param wait_input: if True task only completed when user gives input
        :param delay: time to wait before continuing to the next task
        :param linear_velocity: velocity to move at in [mm/s] (valid for "move line" tasks)
        :param tool: tool attached to robot (valid for hand-guide tasks)
        :return: updated operation
        """
        encoded_name = self._encode_str(task_name)
        encoded_position = self._encode_str(position)
        try:
            return self._task_data.update_operation(encoded_name, index, operation_type, encoded_position, wait_input,
                                                    delay, linear_velocity, tool)
        except ValueError:
            raise

    def delete_operation(self, task_name: str, index: int):
        """
        Delete operation from task.

        :param task_name: task to delete operation from
        :param index: index of operation to be deleted
        """
        encoded_name = self._encode_str(task_name)
        try:
            self._task_data.delete_operation(encoded_name, index)
        except ValueError:
            raise

    def add_position(self, task_name: str, position_name: str, cartesian, joints) -> str:
        """
        Add position to task.

        :param task_name: task name where position will be added
        :param position_name: position name
        :param cartesian: cartesian coordinates
        :param joints: joint positions
        """
        encoded_task_name = self._encode_str(task_name)
        position_name = self._validate_str(position_name)
        encoded_position_name = self._encode_str(position_name)
        if encoded_position_name == "":
            raise ValueError(f"Name {position_name} is not valid! Make sure it has characters that are not space "
                             f"and underscore")
        try:
            self._task_data.add_position(encoded_task_name, encoded_position_name, cartesian, joints)
        except ValueError:
            raise
        return position_name

    def update_position(self, task_name: str, position_name: str, cartesian: list, joints: list):
        """
        Update position values.

        :param task_name: task name where position is stored
        :param position_name: position name to update
        :param cartesian: new cartesian coordinates
        :param joints: joint positions
        """
        encoded_task_name = self._encode_str(task_name)
        encoded_position_name = self._encode_str(position_name)
        try:
            self._task_data.update_position(encoded_task_name, encoded_position_name, cartesian, joints)
        except ValueError:
            raise

    def delete_position(self, task_name: str, position_name: str):
        """
        Delete position from task.

        :param task_name: task name where position will be deleted from
        :param position_name: name of position to delete
        """
        encoded_task_name = self._encode_str(task_name)
        encoded_position_name = self._encode_str(position_name)
        try:
            self._task_data.delete_position(encoded_task_name, encoded_position_name)
        except ValueError:
            raise

    def get_position_names(self, task_name: str) -> list:
        """
        Get names of all positions in given task.

        :param task_name: name of task
        :return: list of position names
        """
        encoded_task = self._encode_str(task_name)
        try:
            return self._decode_str_list(self._task_data.get_position_names(encoded_task))
        except ValueError:
            raise

    def get_operation(self, task_name: str, operation_index: int) -> dict:
        """
        Get operation by index of operation and task name.

        :param task_name: name of task
        :param operation_index: index of operation
        :return: operation
        """
        encoded_task = self._encode_str(task_name)
        try:
            operation = self._task_data.get_operation(encoded_task, operation_index)
            operation["position"] = self._decode_str(operation["position"])
            return operation
        except ValueError:
            raise

    def get_position(self, task_name: str, position_name: str) -> dict:
        """
        Get position by position name and task name.

        :param task_name: task name
        :param position_name: position name
        :return: position's cartesian coordinates and joint positions
        """
        encoded_task = self._encode_str(task_name)
        encoded_position = self._encode_str(position_name)
        try:
            return self._task_data.get_position(encoded_task, encoded_position)
        except ValueError:
            raise

    def start_robot_connection(self, ip: str) -> str:
        """
        Initiate connection with kuka robot.

        :param ip: ip of robot to connect to
        :return: return validated ip
        """
        try:
            return self._robot.start_connection(ip)
        except OSError:
            raise
        except ValueError:
            raise

    def stop_robot_connection(self):
        """
        Stop communication to Kuka robot.
        """
        self._robot.stop_connection()

    def is_robot_connected(self) -> bool:
        """
        Check if a communication is open.

        :return: True if there is an open communication with a Kuka robot
        """
        return self._robot.is_connected()

    def get_robot_position(self) -> tuple:
        """
        Get current robot position.

        :return: cartesian coordinates and joint positions
        """
        try:
            position = self._robot.get_position()
        except OSError:
            raise
        except ValueError:
            raise

        return position

    def run_task(self, task_name: str) -> bool:
        """
        Run task from name.

        :param task_name: name of task to run
        :return: True if user wants to continue running program, False if user wants to stop program
        """

        ready_to_continue = True

        # load task if not yet loaded
        try:
            task = self._task_data.get_task_info(task_name)
        except ValueError:
            self._task_data.load_task(task_name)
            task = self._task_data.get_task_info(task_name)

        for operation in task["operations"]:

            # if "move line" send command to move robot
            if operation["type"] == "move line":
                try:
                    position = self.get_position(task_name, operation["position"])
                    self.move_robot_line(position["cartesian"], operation["linear_velocity"])
                except ValueError:
                    raise
                except OSError:
                    raise

            # if "hand-guide" start hand-guide mode with required tool
            elif operation["type"] == "hand-guide":
                try:
                    tool = self._robot.get_tool_info(operation["tool"])
                    self.hand_guide(weight_of_tool=tool["weight_of_tool"], centre_of_mass=tool["centre_of_mass"])
                except OSError:
                    raise
                except ValueError:
                    raise

            # if "open" open gripper
            elif operation["type"] == "open":
                try:
                    self.open_gripper()
                except OSError:
                    raise

            # if "close" close gripper
            elif operation["type"] == "close":
                try:
                    self.close_gripper()
                except OSError:
                    raise

            time.sleep(operation["delay"])

            # if "wait", open window to wait for input
            if operation["wait"]:
                ready = input("Ready to continue? (Y) - Continue, (N) - Stop")
                if ready == "N" or ready == "n":
                    ready_to_continue = False
                    return ready_to_continue
        return True

    def is_task_up_to_date(self, task_name: str) -> bool:
        """
        Get state of task.

        :param task_name: task name
        :return: True if task is up to date, False otherwise
        """
        encoded_task = self._encode_str(task_name)
        try:
            return self._task_data.is_task_up_to_date(encoded_task)
        except ValueError:
            raise

    def exists_task_file(self, task_name: str) -> tuple:
        """
        Check if file exists.

        :param task_name: task name
        :return: True if file exists, False otherwise
        """
        return self._task_data.file_manager.json_file_exists(self._encode_str(task_name))

    def _get_task_state_from_input(self, encoded_task_name: str) -> int:
        """
        Get task state.

        :return: 0 task exists, 1 task exists but not up to date, 2 task doesn't exist
        """
        if self._task_data.exists_task(encoded_task_name):
            state = 0 if self.is_task_up_to_date(encoded_task_name) else 1
        else:
            state = 0 if self.exists_task_file(encoded_task_name) else 2
        return state

    def move_robot(self, position: list, velocity: float) -> None:
        """
        Move robot's EEF the given amount relative to the base at the given speed.

        :param position: EEF position shift relative to base [x, y, z]
        :param velocity: velocity in [mm/s]
        """
        try:
            self._robot.move_robot(position, velocity)
        except ValueError:
            raise
        except OSError:
            raise

    def move_robot_line(self, position: list, velocity: float) -> None:
        """
        Move robot to the given position at the gicen speed.

        :param position: final position of the robot [x, y, z, a, b, c]
        :param velocity: velocity in [mm/s]
        """
        try:
            self._robot.move_robot_line(position, velocity)
        except ValueError:
            raise
        except OSError:
            raise

    def open_gripper(self) -> None:
        """
        Open gripper (Pin 11).
        """
        try:
            self._robot.open_gripper()
        except OSError:
            raise

    def close_gripper(self) -> None:
        """
        Open gripper (Pin 11).
        """
        try:
            self._robot.close_gripper()
        except OSError:
            raise

    def hand_guide(self, weight_of_tool: float, centre_of_mass: list) -> None:
        """
        Start hand-guiding mode.

        :param weight_of_tool: weight of the tool in Newtons
        :param centre_of_mass: centre of mass of the tool [x, y, z] in [mm]
        """
        try:
            self._robot.hand_guide(weight_of_tool, centre_of_mass)
        except OSError:
            raise
        except ValueError:
            raise

    def get_tool_names(self) -> list:
        """
        Get names of existing tools.

        :return: names of tools
        """
        return self._robot.get_tool_names()

    def get_tool_info(self, tool: str) -> dict:
        """
        Get weight and centre of mass of given tool.

        :param tool: name of the tool
        :return: weight and centre of mass
        """
        try:
            return self._robot.get_tool_info(tool)
        except ValueError:
            raise

    def exists_task(self, task: str) -> bool:
        """
        Check if task exists.

        :param task: name of task
        :return: True if task exists
        """

        task = self._encode_str(task)
        return self._task_data.exists_task(task)

    def load_all_tasks(self) -> None:
        """
        Load all tasks
        """

        self._task_data.load_all_tasks()




