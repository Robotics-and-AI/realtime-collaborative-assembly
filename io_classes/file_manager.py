import json
import os
from typing import Union

import matplotlib.backends.backend_pdf
import numpy as np
from matplotlib.figure import Figure


class NumpyEncoder(json.JSONEncoder):
    """ Special json encoder for numpy types """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, np.bool_):
            return bool(obj)
        return f"<<non-serializable: {type(obj).__qualname__}>>"


# class for file management
class FileManager:
    def __init__(self, path: str):
        # directory where files are saved
        self.path = path

    def directory_exists(self, directory_name: str) -> bool:
        """
        Check if directory exists.

        :param directory_name: file name
        :return: True if file exists, False otherwise
        """

        return os.path.exists(os.path.join(self.path, directory_name))

    def json_file_exists(self, file_name: str) -> bool:
        """
        Check if file exists.

        :param file_name: file name
        :return: True if file exists, False otherwise
        """
        return os.path.exists(os.path.join(self.path, f"{file_name}.json"))

    def save_json_file(self, file_name: str, file_data: Union[list, dict]) -> None:
        """
        Save given data to the specified file.

        :param file_name: file to save to
        :param file_data: data to save
        """
        with open(os.path.join(self.path, f"{file_name}.json"), "w+") as file:
            json.dump(file_data, file, indent=2, sort_keys=True, cls=NumpyEncoder)

    def load_json_file(self, file_name: str) -> Union[list, dict]:
        """
        Load file.

        :param file_name: name of the file to load from
        :return: data read on the specified file
        """
        if self.json_file_exists(file_name):
            with open(os.path.join(self.path, f"{file_name}.json")) as file:
                return json.load(file)
        else:
            raise FileNotFoundError(f"There is no file {file_name}.json")

    def npy_file_exists(self, file_name: str) -> bool:
        """
        Check if file exists.

        :param file_name: file name
        :return: True if file exists, False otherwise
        """
        return os.path.exists(os.path.join(self.path, f"{file_name}.npy"))

    def save_npy_file(self, file_name: str, file_data: np.array) -> None:
        """
        Save given data to the specified file.

        :param file_name: file to save to
        :param file_data: data to save
        """
        np.save(os.path.join(self.path, f"{file_name}.npy"), file_data)

    def load_npy_file(self, file_name: str) -> np.array:
        """
        Load file.

        :param file_name: name of the file to load from
        :return: data read on the specified file
        """
        if self.npy_file_exists(file_name):
            return np.load(os.path.join(self.path, f"{file_name}.npy"))
        else:
            raise FileNotFoundError(f"There is no file {file_name}.npy")

    def delete_file(self, file_name: str) -> None:
        """
        Delete file with given name.

        :param file_name: name of file to be deleted
        """
        if self.json_file_exists(file_name):
            os.remove(os.path.join(self.path, f"{file_name}.json"))

    def update_path(self, path) -> None:
        """
        Update output path.

        :param path: new path to output files to
        """
        if isinstance(path, str):
            self.path = path
        elif isinstance(path, list):
            self.path = os.path.join(*path)
        else:
            raise TypeError("When providing a path, either enter entire path, or list of folders!")

    def save_plots_to_pdf(self, pdf_name: str, figures: list):
        """
        Save plots to pdf file.

        :param pdf_name: file name
        :param figures: list of figures to save
        """

        # check if all figures are the correct type
        for figure in figures:
            if not isinstance(figure, Figure):
                raise TypeError("Plot must be of type Figure")

        # open pdf file and save each figure
        pdf = matplotlib.backends.backend_pdf.PdfPages(os.path.join(self.path, f"{pdf_name}.pdf"))
        for figure in figures:
            pdf.savefig(figure)
        pdf.close()

    def create_directory(self, directory_name: str) -> None:
        """
        Create new directory if it doesn't exist.

        :param directory_name: New directory name
        """

        path = os.path.join(self.path, directory_name)
        if os.path.exists(path):
            raise OSError("Directory already exists")

        os.makedirs(path)
        self.update_path(path)
