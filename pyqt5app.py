import sys
from PyQt5 import QtWidgets, uic
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtGui, QtCore
from PyQt5.QtCore import *

import os
import globus_utils
import globus_sdk

import yaml

from globus_compute_sdk import Client, Executor
from globus_compute_sdk.serialize import CombinedCode

from globus_compute_util import list_dir, list_cpu, remove_files, run_command

from pathlib import Path
from typing import List

from preview_data_dialog import ImageDialog

from enum import Enum
class MessageLevel(Enum):
    WARNING = 1
    INFO = 2
    SUCCESS = 3
    ALERT = 4

class TransferThread(QThread):
    def __init__(self, transfer_client, transfer_document):
        super().__init__()
        self.tc = transfer_client
        self.transfer_document = transfer_document
        self.task_id = self.transfer_document["task_id"]

    def run(self):
        while not self.tc.task_wait(self.task_id, timeout=10):
            print(f"another 10 seconds have passed waiting for transfer task {self.task_id} to complete!")
        self.finished.emit()

class CompressorCmdFactory():
    @staticmethod
    def make_sz3_compress_cmd(excutable, filename, compressedFilename, dimension: List, mode, errorbound) -> str:
        command = [excutable, "-f", "-i", filename,
                   "-z", compressedFilename, "-M", mode,
                   errorbound, f"-{len(dimension)}"] + dimension
        command_str = " ".join(command)
        return command_str
    
    @staticmethod
    def make_sz3_decompress_cmd(executable, filename, decompressedFilename, dimension: List, mode, errorbound) -> str:
        command = [executable, "-f", "-z", filename,
                   "-o", decompressedFilename, "-M", mode,
                   errorbound, f"-{len(dimension)}"] + dimension
        command_str = " ".join(command)
        return command_str
        

class UI(QDialog):
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi("ocelot.ui", self)

        self.globus_client_id = "1fb9c8a9-1aff-4d46-9f37-e3b0d44194f2"
        self.globus_token_filename = "globus_tokens.json"

        # Machine A Config
        self.funcx_id_lineedit_a = self.findChild(QLineEdit, "funcx_id_lineedit_a")
        self.globus_id_lineedit_a = self.findChild(QLineEdit, "globus_id_lineedit_a")
        self.workdir_lineedit_a = self.findChild(QLineEdit, "workdir_lineedit_a")

        self.register_globus_compute_button_a = self.findChild(QPushButton, "register_globus_compute_button_a")
        self.remove_files_button_a = self.findChild(QPushButton, "remove_files_button_a")
        self.list_workdir_button_a = self.findChild(QPushButton, "list_workdir_button_a")
        self.save_config_button_a = self.findChild(QPushButton, "save_config_button_a")
        self.load_config_button_a = self.findChild(QPushButton, "load_config_button_a")
        self.compress_button_a = self.findChild(QPushButton, "compress_button_a")
        self.decompress_button_a = self.findChild(QPushButton, "decompress_button_a")
        self.transfer_button_a = self.findChild(QPushButton, "transfer_button_a")
        self.auto_transfer_button_a = self.findChild(QPushButton, "auto_transfer_button_a")

        self.workdir_listwidget_a = self.findChild(QListWidget, "workdir_listwidget_a")
        self.workdir_listwidget_a.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.workdir_listwidget_a.itemSelectionChanged.connect(self.on_listwidget_item_changed_a)

        # Machine B Config
        self.funcx_id_lineedit_b = self.findChild(QLineEdit, "funcx_id_lineedit_b")
        self.globus_id_lineedit_b = self.findChild(QLineEdit, "globus_id_lineedit_b")
        self.workdir_lineedit_b = self.findChild(QLineEdit, "workdir_lineedit_b")

        self.register_globus_compute_button_b = self.findChild(QPushButton, "register_globus_compute_button_b")
        self.remove_files_button_b = self.findChild(QPushButton, "remove_files_button_b")
        self.list_workdir_button_b = self.findChild(QPushButton, "list_workdir_button_b")
        self.save_config_button_b = self.findChild(QPushButton, "save_config_button_b")
        self.load_config_button_b = self.findChild(QPushButton, "load_config_button_b")
        self.compress_button_b = self.findChild(QPushButton, "compress_button_b")
        self.decompress_button_b = self.findChild(QPushButton, "decompress_button_b")
        self.transfer_button_b = self.findChild(QPushButton, "transfer_button_b")
        self.auto_transfer_button_b = self.findChild(QPushButton, "auto_transfer_button_b")

        self.workdir_listwidget_b = self.findChild(QListWidget, "workdir_listwidget_b")
        self.workdir_listwidget_b.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.workdir_listwidget_b.itemSelectionChanged.connect(self.on_listwidget_item_changed_b)

        # Globus Transfer Authentication
        self.authenticate_button = self.findChild(QPushButton, "authenticate_button")
        self.authenticate_status_label= self.findChild(QLabel, "authenticate_status_label")

        # Button Callback Connection
        self.authenticate_button.clicked.connect(self.on_click_authenticate_button)
        self.list_workdir_button_a.clicked.connect(self.on_click_list_workdir_button_a)
        self.save_config_button_a.clicked.connect(self.on_click_save_config_button_a)
        self.load_config_button_a.clicked.connect(self.on_click_load_config_button_a)
        self.compress_button_a.clicked.connect(self.on_click_compress_button_a)
        self.decompress_button_a.clicked.connect(self.on_click_decompress_button_a)
        self.transfer_button_a.clicked.connect(self.on_click_transfer_button_a)
        self.auto_transfer_button_a.clicked.connect(self.on_click_autotransfer_button_a)

        self.list_workdir_button_b.clicked.connect(self.on_click_list_workdir_button_b)
        self.save_config_button_b.clicked.connect(self.on_click_save_config_button_b)
        self.load_config_button_b.clicked.connect(self.on_click_load_config_button_b)
        self.compress_button_b.clicked.connect(self.on_click_compress_button_b)
        self.decompress_button_b.clicked.connect(self.on_click_decompress_button_b)
        self.transfer_button_b.clicked.connect(self.on_click_transfer_button_b)
        self.auto_transfer_button_b.clicked.connect(self.on_click_autotransfer_button_b)
        
        self.register_globus_compute_button_a.clicked.connect(self.on_click_register_globus_compute_a)
        self.register_globus_compute_button_b.clicked.connect(self.on_click_register_globus_compute_b)
        self.remove_files_button_a.clicked.connect(self.on_click_remove_files_button_a)
        self.remove_files_button_b.clicked.connect(self.on_click_remove_files_button_b)


        # Dataset Config
        self.dataset_directory_lineEdit = self.findChild(QLineEdit, "dataset_directory_lineEdit")
        self.list_dataset_button = self.findChild(QPushButton, "list_dataset_button")
        self.preview_data_button = self.findChild(QPushButton, "preview_data_button")
        self.dataset_dir_listWidget = self.findChild(QListWidget, "dataset_dir_listWidget")
        self.machine_a_radio_button = self.findChild(QRadioButton, "machine_a_radio_button")
        self.machine_b_radio_button = self.findChild(QRadioButton, "machine_b_radio_button")
        self.compress_selected_button = self.findChild(QPushButton, "compress_selected_button")
        self.decompress_selected_button = self.findChild(QPushButton, "decompress_selected_button")
        self.transfer_selected_button = self.findChild(QPushButton, "transfer_selected_button")

        self.list_dataset_button.clicked.connect(self.on_click_list_dataset_button)
        self.preview_data_button.clicked.connect(self.on_click_preview_selected_button)
        self.compress_selected_button.clicked.connect(self.on_click_compress_selected_button)
        self.decompress_selected_button.clicked.connect(self.on_click_decompress_selected_button)
        self.transfer_selected_button.clicked.connect(self.on_click_transfer_selected_button)
        self.machine_a_radio_button.toggled.connect(self.on_toggle_machine_a)
        self.machine_b_radio_button.toggled.connect(self.on_toggle_machine_b)

        # Status and Performance
        self.current_status_textEdit = self.findChild(QTextEdit, "current_status_textEdit")
        self.transfer_performance_textEdit = self.findChild(QTextEdit, "transfer_performance_textEdit")

        # Compressor Config
        self.compressorTabWidget = self.findChild(QTabWidget, "compressorTabWdiget")
        self.SZ3_tab = self.compressorTabWidget.findChild(QWidget, "SZ3_tab")
        self.SZ_REGION_tab = self.compressorTabWidget.findChild(QWidget, "SZ_REGION_tab")
        self.ZFP_tab = self.compressorTabWidget.findChild(QWidget, "ZFP_tab")

        # SZ3 config
        self.sz3_data_dimension_lineEdit = self.SZ3_tab.findChild(QLineEdit, "data_dimension_lineEdit")
        self.sz3_error_bound_lineEdit = self.SZ3_tab.findChild(QLineEdit, "error_bound_lineEdit")
        self.sz3_executable_lineEdit_MA = self.SZ3_tab.findChild(QLineEdit, "sz3_executable_lineEdit_MA")
        self.sz3_executable_lineEdit_MB = self.SZ3_tab.findChild(QLineEdit, "sz3_executable_lineEdit_MB")
        self.sz3_eb_mode_abs_radiobutton = self.SZ3_tab.findChild(QRadioButton, "abs_mode_radio_button")
        self.sz3_eb_mode_rel_radiobutton = self.SZ3_tab.findChild(QRadioButton, "rel_radio_button")
        self.sz3_eb_mode_abs_and_rel_radiobutton = self.SZ3_tab.findChild(QRadioButton, "abs_and_rel_radio_button")
        self.sz3_test_executable_button_ma = self.SZ3_tab.findChild(QPushButton, "test_executable_button_ma")
        self.sz3_test_executable_button_ma.clicked.connect(self.on_click_sz3_test_executable_button_ma)
        self.sz3_test_executable_button_mb = self.SZ3_tab.findChild(QPushButton, "test_exectuable_buttom_mb")
        self.sz3_test_executable_button_ma.clicked.connect(self.on_click_sz3_test_executable_button_mb)

        # YAML config information
        self.machine_a_config = None
        self.machine_b_config = None

        # Globus Compute Client
        self.gcc = Client(code_serialization_strategy=CombinedCode())
        # self.list_dir_uuid = self.gcc.register_function(list_dir)
        self.gce_machine_a = None
        self.gce_machine_b = None

        # ListWidget selection
        self.listwidget_a_selected_paths = None
        self.listwidget_b_selected_paths = None

        # Globus Transfer
        self.tc = None

        # Colors
        self.color_effect_darkgreen = QGraphicsColorizeEffect()
        self.color_effect_darkgreen.setColor(Qt.GlobalColor.darkGreen)
        self.color_effect_red = QGraphicsColorizeEffect()
        self.color_effect_red.setColor(Qt.GlobalColor.red)

        # HTML
        self.endHTMLTag = "</font><br>"
        self.alertHTMLTag = "<font color='Red'><br>"
        self.infoHTMLTag = "<font color='Black'><br>"
        self.successHTMLTag = "<font color='Green'><br>"
        self.warningHTMLTag = "<font color='Yellow'><br>"

        # default dataset dir
        self.dataset_dir_a_default = ""
        self.dataset_dir_b_default = ""

        self.show()

    def on_click_sz3_test_executable_button_ma(self):
        data_dimension = self.sz3_data_dimension_lineEdit.text()
        error_bound = self.sz3_error_bound_lineEdit.text()
        executable = self.sz3_executable_lineEdit_MA.text()
        print("data dimension:", data_dimension)
        print("error bound:", error_bound)
        print("exectuable:", executable)
        if self.gce_machine_a is None:
            QMessageBox.information(self, "Test Executable", "You need to register machine A for Globus Compute", QMessageBox.StandardButton.Close)
            return
        future = self.gce_machine_a.submit(run_command, " ".join([executable, "--help"]))
        future.add_done_callback(lambda f: print("Machine A Test Excutable result: ", f.result()))

    def on_click_sz3_test_executable_button_mb(self):
        data_dimension = self.sz3_data_dimension_lineEdit.text()
        error_bound = self.sz3_error_bound_lineEdit.text()
        executable = self.sz3_executable_lineEdit_MB.text()
        print("data dimension:", data_dimension)
        print("error bound:", error_bound)
        print("exectuable:", executable)
        if self.gce_machine_b is None:
            QMessageBox.information(self, "Test Executable", "You need to register machine B for Globus Compute", QMessageBox.StandardButton.Close)
            return
        future = self.gce_machine_b.submit(run_command, " ".join([executable, "--help"]))
        future.add_done_callback(lambda f: print("Machine B Test Excutable result: ", f.result()))

    def put_datasetdir_into_listWidget(self, future, machine):
        self.dataset_dir_listWidget.clear()
        for file in future.result():
            self.dataset_dir_listWidget.addItem(file)
        print(f"List Dataset has completed in machine {machine}")

    def is_globus_compute_registered(self) -> bool:
        if self.gce_machine_a is None or self.gce_machine_b is None:
            return False
        return True
    
    def on_click_list_dataset_button(self):
        if self.machine_a_radio_button.isChecked() and self.gce_machine_a is None:
            QMessageBox.information(self, "List Dataset", "You need to register Globus Compute For Machine A First!", QMessageBox.StandardButton.Close)
            return
        if self.machine_b_radio_button.isChecked() and self.gce_machine_b is None:
            QMessageBox.information(self, "List Dataset", "You need to register Globus Compute For Machine B First!", QMessageBox.StandardButton.Close)
            return
        if not self.machine_a_radio_button.isChecked() and not self.machine_b_radio_button.isChecked():
            QMessageBox.information(self, "List Dataset", "You need to select which machine the dataset is on!", QMessageBox.StandardButton.Close)
            return
        
        if self.machine_a_radio_button.isChecked():
            future = self.gce_machine_a.submit(list_dir, self.dataset_directory_lineEdit.text().strip())
            machine = "A"
        else:
            future = self.gce_machine_b.submit(list_dir, self.dataset_directory_lineEdit.text().strip())
            machine = "B"
        future.add_done_callback(lambda f: self.put_datasetdir_into_listWidget(f, machine))
        print(f"submitted request to list dataset for machine {machine}")
    
    def on_click_preview_selected_button(self):
        gce = None
        filename = self.dataset_dir_listWidget.selectedItems()[0].text()
        if self.machine_a_radio_button.isChecked():
            gce = self.gce_machine_a
        elif self.machine_b_radio_button.isChecked():
            gce = self.gce_machine_b
        dimension = self.sz3_data_dimension_lineEdit.text()
        filepath = str(Path(self.dataset_directory_lineEdit.text()) / filename) 
        preview_dialog = ImageDialog(gce=gce, dataDimension=dimension, file_path=filepath)
        if preview_dialog.exec_() == QDialog.Accepted:
            self.rects = preview_dialog.getRects()
            self.ranges = preview_dialog.getRanges()
            print("Rects from preview: ", self.rects)
            print("Ranges from preview: ", self.ranges)
        else:
            print("Use clicked cancel in the preview dialog")

    def on_click_compress_button_a(self):
        dimension = self.sz3_data_dimension_lineEdit.text().split()
        errorbound = self.sz3_error_bound_lineEdit.text()
        mode = "REL" if self.sz3_eb_mode_rel_radiobutton.isChecked() else "ABS"
        if self.sz3_eb_mode_abs_and_rel_radiobutton.isChecked():
            mode = "ABS_AND_REL"
        if len(self.workdir_listwidget_a.selectedItems()) != 1:
            QMessageBox.information(self, "Compress", "Please select only one file for compression", QMessageBox.StandardButton.Close)
            return
        if self.gce_machine_a is None:
            QMessageBox.information(self, "Compress", "You need to register Globus Compute for machine A first", QMessageBox.StandardButton.Close)
            return
        filename = self.workdir_listwidget_a.selectedItems()[0].text()
        filepath = str(Path(self.workdir_lineedit_a.text()) / filename)
        executable = self.sz3_executable_lineEdit_MA.text()
        compressed_filename = str(Path(self.workdir_lineedit_a.text()) / (filename + ".sz"))
        command = CompressorCmdFactory.make_sz3_compress_cmd(executable, filepath, compressed_filename, dimension, mode, errorbound)
        future = self.gce_machine_a.submit(run_command, command)
        print("Machine A compression task has been submitted")
        future.add_done_callback(lambda f: (print("machine A compression result:", f.result()), self.on_click_list_workdir_button_a()))
        QMessageBox.information(self, "Compress", "The compression task on Machine A has been submitted!", QMessageBox.StandardButton.Close)

    def on_click_compress_button_b(self):
        dimension = self.sz3_data_dimension_lineEdit.text().split()
        errorbound = self.sz3_error_bound_lineEdit.text()
        mode = "REL" if self.sz3_eb_mode_rel_radiobutton.isChecked() else "ABS"
        if self.sz3_eb_mode_abs_and_rel_radiobutton.isChecked():
            mode = "ABS_AND_REL"
        if len(self.workdir_listwidget_b.selectedItems()) != 1:
            QMessageBox.information(self, "Compress", "Please select only one file for compression", QMessageBox.StandardButton.Close)
            return
        if self.gce_machine_b is None:
            QMessageBox.information(self, "Compress", "You need to register Globus Compute for machine B first", QMessageBox.StandardButton.Close)
            return
        filename = self.workdir_listwidget_b.selectedItems()[0].text()
        filepath = str(Path(self.workdir_lineedit_b.text()) / filename)
        executable = self.sz3_executable_lineEdit_MB.text()
        compressed_filename = str(Path(self.workdir_lineedit_b.text()) / (filename + ".sz"))
        command = CompressorCmdFactory.make_sz3_compress_cmd(executable, filepath, compressed_filename, dimension, mode, errorbound)
        future = self.gce_machine_b.submit(run_command, command)
        print("Machine B compression task has been submitted")
        future.add_done_callback(lambda f: (print("machine B compression result:", f.result()), self.on_click_list_workdir_button_b()))
        QMessageBox.information(self, "Compress", "The compression task on Machine B has been submitted!", QMessageBox.StandardButton.Close)

    def on_click_decompress_button_a(self):
        dimension = self.sz3_data_dimension_lineEdit.text().split()
        errorbound = self.sz3_error_bound_lineEdit.text()
        mode = "REL" if self.sz3_eb_mode_rel_radiobutton.isChecked() else "ABS"
        if self.sz3_eb_mode_abs_and_rel_radiobutton.isChecked():
            mode = "ABS_AND_REL"
        if len(self.workdir_listwidget_a.selectedItems()) != 1:
            QMessageBox.information(self, "Decompress", "Please select only one file for compression", QMessageBox.StandardButton.Close)
            return
        if self.gce_machine_a is None:
            QMessageBox.information(self, "Decompress", "You need to register Globus Compute for machine A first", QMessageBox.StandardButton.Close)
            return
        filename = self.workdir_listwidget_a.selectedItems()[0].text()
        filepath = str(Path(self.workdir_lineedit_a.text()) / filename)
        executable = self.sz3_executable_lineEdit_MA.text()
        decompressed_filename = str(Path(self.workdir_lineedit_a.text()) / (filename + ".dp"))
        command = CompressorCmdFactory.make_sz3_decompress_cmd(executable, filepath, decompressed_filename, dimension, mode, errorbound)
        future = self.gce_machine_a.submit(run_command, command)
        print("Machine A decompression task has been submitted")
        future.add_done_callback(lambda f: (print("machine A decompression result:", f.result()), self.on_click_list_workdir_button_a()))

        QMessageBox.information(self, "Decompress", "The decompression task on machine A has been submitted!", QMessageBox.StandardButton.Close)

    def on_click_decompress_button_b(self):
        dimension = self.sz3_data_dimension_lineEdit.text().split()
        errorbound = self.sz3_error_bound_lineEdit.text()
        mode = "REL" if self.sz3_eb_mode_rel_radiobutton.isChecked() else "ABS"
        if self.sz3_eb_mode_abs_and_rel_radiobutton.isChecked():
            mode = "ABS_AND_REL"
        if len(self.workdir_listwidget_b.selectedItems()) != 1:
            QMessageBox.information(self, "Decompress", "Please select only one file for compression", QMessageBox.StandardButton.Close)
            return
        if self.gce_machine_b is None:
            QMessageBox.information(self, "Decompress", "You need to register Globus Compute for machine A first", QMessageBox.StandardButton.Close)
            return
        filename = self.workdir_listwidget_b.selectedItems()[0].text()
        filepath = str(Path(self.workdir_lineedit_b.text()) / filename)
        executable = self.sz3_executable_lineEdit_MB.text()
        decompressed_filename = str(Path(self.workdir_lineedit_b.text()) / (filename + ".dp"))
        command = CompressorCmdFactory.make_sz3_decompress_cmd(executable, filepath, decompressed_filename, dimension, mode, errorbound)
        future = self.gce_machine_b.submit(run_command, command)
        print("Machine B decompression task has been submitted")
        future.add_done_callback(lambda f: (print("machine B decompression result:", f.result()), self.on_click_list_workdir_button_b()))
        QMessageBox.information(self, "Decompress", "The decompression task on machine B has been submitted!", QMessageBox.StandardButton.Close)

    def _compress_selected_callback(self, future, machine):
        print("compression result:", future.result())
        if machine == "A":
            self.on_click_list_workdir_button_a()
            print("submitted a request to list workdir a")
        else:
            self.on_click_list_workdir_button_b()
            print("submitted a request to list workdir b")


    def on_click_compress_selected_button(self):
        
        dimension = self.sz3_data_dimension_lineEdit.text().split()
        errorbound = self.sz3_error_bound_lineEdit.text()
        mode = "REL" if self.sz3_eb_mode_rel_radiobutton.isChecked() else "ABS"
        if self.sz3_eb_mode_abs_and_rel_radiobutton.isChecked():
            mode = "ABS_AND_REL"
        filename = self.dataset_dir_listWidget.selectedItems()[0].text()
        
        if self.machine_a_radio_button.isChecked():
            compressed_filename = str(Path(self.workdir_lineedit_a.text()) / (filename + ".sz"))
            executable = self.sz3_executable_lineEdit_MA.text()
        elif self.machine_b_radio_button.isChecked():
            compressed_filename = str(Path(self.workdir_lineedit_b.text()) / (filename + ".sz"))
            executable = self.sz3_executable_lineEdit_MB.text()
        else:
            print("neither machine a or b is checked")
        filepath = str(Path(self.dataset_directory_lineEdit.text()) / filename) 
        command = CompressorCmdFactory.make_sz3_compress_cmd(executable, filepath, compressed_filename, dimension, mode, errorbound)
        print("the sz3 compress command:", command)
        if self.machine_a_radio_button.isChecked():
            future = self.gce_machine_a.submit(run_command, command)
            machine = "A"
        else:
            future = self.gce_machine_b.submit(run_command, command)
            machine = "B"
        print("compression task has been submitted!")
        future.add_done_callback(lambda f: self._compress_selected_callback(f, machine))
        QMessageBox.information(self, "Compress Selected", "The compression task has been submitted!", QMessageBox.StandardButton.Close)
    
    def on_click_decompress_selected_button(self):
        dimension = self.sz3_data_dimension_lineEdit.text().split()
        errorbound = self.sz3_error_bound_lineEdit.text()
        mode = "REL" if self.sz3_eb_mode_rel_radiobutton.isChecked() else "ABS"
        if self.sz3_eb_mode_abs_and_rel_radiobutton.isChecked():
            mode = "ABS_AND_REL"
        filename = self.dataset_dir_listWidget.selectedItems()[0].text()
        if self.machine_a_radio_button.isChecked():
            decompressed_filename = str(Path(self.workdir_lineedit_a.text()) / (filename + ".dp"))
            executable = self.sz3_executable_lineEdit_MA.text()
        elif self.machine_b_radio_button.isChecked():
            decompressed_filename = str(Path(self.workdir_lineedit_b.text()) / (filename + ".dp"))
            executable = self.sz3_executable_lineEdit_MB.text()
        else:
            print("neither machine a or b is checked")
        filepath = str(Path(self.dataset_directory_lineEdit.text()) / filename) 
        command = CompressorCmdFactory.make_sz3_decompress_cmd(executable, filepath, decompressed_filename, dimension, mode, errorbound)
        if self.machine_a_radio_button.isChecked():
            future = self.gce_machine_a.submit(run_command, command)
        else:
            future = self.gce_machine_b.submit(run_command, command)
        print("decompression task has been submitted!")
        future.add_done_callback(lambda f: print("decompression result:", f.result()))
        QMessageBox.information(self, "Decompress Selected", "You clicked the decompress selected button", QMessageBox.StandardButton.Close)
    
    def on_click_transfer_selected_button(self):
        QMessageBox.information(self, "Transfer Selected", "You clicked the transfer selected button", QMessageBox.StandardButton.Close)

    def on_click_register_globus_compute_a(self):
        self.gce_machine_a = Executor(endpoint_id=self.funcx_id_lineedit_a.text().strip(), funcx_client=self.gcc)
        future = self.gce_machine_a.submit(list_cpu)
        print("submitted a lscpu to machine A")
        future.add_done_callback(lambda f: print("Machine A CPU Info:\n", f.result()))

    def on_click_register_globus_compute_b(self):
        self.gce_machine_b = Executor(endpoint_id=self.funcx_id_lineedit_b.text().strip(), funcx_client=self.gcc)
        future = self.gce_machine_b.submit(list_cpu)
        print("submitted a lscpu to machine B")
        future.add_done_callback(lambda f: print("Machine B CPU Info:\n", f.result()))

    def on_click_authenticate_button(self):
        collections = [self.globus_id_lineedit_a.text().strip(), self.globus_id_lineedit_b.text().strip()]
        cwd = os.getcwd()
        globus_client_id = self.globus_client_id 
        print('globus client id:',globus_client_id)
        try:
            self.globus_authorizer = globus_utils.get_proxystore_authorizer(globus_client_id, self.globus_token_filename, cwd)
            self.tc = globus_sdk.TransferClient(authorizer=self.globus_authorizer)
        except globus_utils.GlobusAuthFileError:
            print(
                'Performing authentication for the Ocelot app.',
            )
            globus_utils.proxystore_authenticate(
                w=self,
                client_id=globus_client_id,
                token_file_name=self.globus_token_filename,
                proxystore_dir=cwd,
                collections=collections,
            )
            self.globus_authorizer = globus_utils.get_proxystore_authorizer(globus_client_id, self.globus_token_filename, cwd)
            self.tc = globus_sdk.TransferClient(authorizer=self.globus_authorizer)
            print('Globus authorization complete.')
        else:
            print(
                'Globus authorization is already completed. To re-authenticate, '
                'delete your tokens and try again'
            )
        self.authenticate_status_label.setText("Authenticated!")
        self.authenticate_status_label.setGraphicsEffect(self.color_effect_darkgreen)

        QMessageBox.information(self, "Authenticate", "You have finished Globus Transfer Autentication", QMessageBox.StandardButton.Close)

    def remove_files_callback(self, future, machine):
        success = future.result()
        if success:
            print(f"the files have been removed! on machine {machine}")
        else:
            print("the file removal was not successful!")
        if machine == 'A':
            self.on_click_list_workdir_button_a()
        elif machine == 'B':
            self.on_click_list_workdir_button_b()

    def on_click_remove_files_button_a(self):
        reply = QMessageBox.question(self, "Remove Files", "Are you sure you want to remove selected files in Machine A?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            print("Confirmed to remove files in Machine A")
        else:
            print("Removing files in machine A is canceled")
            return
        if len(self.listwidget_a_selected_paths) > 0:
            future = self.gce_machine_a.submit(remove_files, self.listwidget_a_selected_paths)
            future.add_done_callback(lambda f: self.remove_files_callback(f, "A"))
        else:
            print("You haven't selected files to remove!")


    def on_click_remove_files_button_b(self):
        reply = QMessageBox.question(self, "Remove Files", "Are you sure you want to remove selected files in Machine B?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            print("Confirmed to remove files in Machine B")
        else:
            print("Removing files in machine B is canceled")
            return
        if len(self.listwidget_b_selected_paths) > 0:
            future = self.gce_machine_b.submit(remove_files, self.listwidget_b_selected_paths)
            future.add_done_callback(lambda f: self.remove_files_callback(f, "B"))
        else:
            print("You haven't selected files to remove!")


    def on_listwidget_item_changed_a(self):
        self.listwidget_a_selected_paths = [Path(self.workdir_lineedit_a.text().strip()) / item.text().strip()
                                           for item in self.workdir_listwidget_a.selectedItems()]
        print("list widget a selected:", self.listwidget_a_selected_paths)

    def on_listwidget_item_changed_b(self):
        self.listwidget_b_selected_paths = [Path(self.workdir_lineedit_b.text().strip()) / item.text().strip()
                                           for item in self.workdir_listwidget_b.selectedItems()]
        print("list widget b selected:", self.listwidget_b_selected_paths)

    def put_workdir_into_listWidget_a(self, future):
        self.workdir_listwidget_a.clear()
        for file in future.result():
            self.workdir_listwidget_a.addItem(file)
        print("List Workdir has completed in machine A")

    def put_workdir_into_listWidget_b(self, future):
        self.workdir_listwidget_b.clear()
        for file in future.result():
            self.workdir_listwidget_b.addItem(file)
        print("List Workdir has completed in machine B")

    def on_click_list_workdir_button_a(self):
        if self.gce_machine_a is None:
            QMessageBox.information(self, "List Workdir", "You need to register Globus Compute First!", QMessageBox.StandardButton.Close)
            return
        future = self.gce_machine_a.submit(list_dir, self.workdir_lineedit_a.text().strip())
        future.add_done_callback(lambda f: self.put_workdir_into_listWidget_a(f))
        print("submitted request to list workdir for machine A")
        # QMessageBox.information(self, "List Workdir", "You clicked the List Workdir A button!", QMessageBox.StandardButton.Close)

    def on_click_list_workdir_button_b(self):
        if self.gce_machine_b is None:
            QMessageBox.information(self, "List Workdir", "You need to register Globus Compute First!", QMessageBox.StandardButton.Close)
            return
        future = self.gce_machine_b.submit(list_dir, self.workdir_lineedit_b.text().strip())
        future.add_done_callback(lambda f: self.put_workdir_into_listWidget_b(f))
        print("submitted request to list workdir for machine B")
        # QMessageBox.information(self, "List Workdir", "You clicked the List Workdir B button!", QMessageBox.StandardButton.Close)

    def on_click_save_config_button_a(self):
        machine_config_file, ok = QFileDialog.getSaveFileName(self, "Save As", os.getcwd(), "YAML files (*.yaml *.yml)")
        if not ok:
            return
        
        with open(machine_config_file, 'w') as f:
            try:
                yaml.dump(self.machine_a_config, f, default_flow_style=False)
            except yaml.YAMLError as exec:
                print("cannot save the YAML file")
                return

        QMessageBox.information(self, "Save Config", "You have successfully saved the config file for machine A", QMessageBox.StandardButton.Ok)

    def on_click_save_config_button_b(self):
        machine_config_file, ok = QFileDialog.getSaveFileName(self, "Save As", os.getcwd(), "YAML files (*.yaml *.yml)")
        if not ok:
            return
        
        with open(machine_config_file, 'w') as f:
            try:
                yaml.dump(self.machine_b_config, f, default_flow_style=False)
            except yaml.YAMLError as exec:
                print("cannot save the YAML file")
                return

        QMessageBox.information(self, "Save Config", "You have successfully saved the config file for machine B", QMessageBox.StandardButton.Ok)

    def on_toggle_machine_a(self, checked):
        if checked:
            self.dataset_directory_lineEdit.setText(self.dataset_dir_a_default)
        else:
            self.dataset_dir_a_default = self.dataset_directory_lineEdit.text()
    
    def on_toggle_machine_b(self, checked):
        if checked:
            self.dataset_directory_lineEdit.setText(self.dataset_dir_b_default)
        else:
            self.dataset_dir_b_default = self.dataset_directory_lineEdit.text()

    def on_click_load_config_button_a(self):
        machine_config_file, ok = QFileDialog.getOpenFileName(self, "Open", os.getcwd(), "YAML files (*.yaml *.yml)")
        if not ok:
            return
        
        with open(machine_config_file, 'r') as f:
            try:
                self.machine_a_config = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                print("Cannot load YAML config for machine a")
                QMessageBox.information(self, "Load Config", "Failed to load config file for machine A", QMessageBox.StandardButton.Close)
                return
        try:
            self.funcx_id_lineedit_a.setText(self.machine_a_config["globus_compute_id"])
            self.globus_id_lineedit_a.setText(self.machine_a_config["globus_transfer_id"])
            self.workdir_lineedit_a.setText(self.machine_a_config["work_dir"])
        except KeyError:
            QMessageBox.warning(self, "Config Error", "Config file not correct!", QMessageBox.StandardButton.Cancel)
        
        if "defaults" in self.machine_a_config:
            defaults = self.machine_a_config["defaults"]
            if "sz3_exe" in defaults:
                self.sz3_exe_a = defaults["sz3_exe"]
                self.sz3_executable_lineEdit_MA.setText(self.sz3_exe_a)
            if "dataset_dir" in defaults:
                self.dataset_dir_a_default = defaults["dataset_dir"]

        if "globus_client_id" in self.machine_a_config:
            self.globus_client_id = self.machine_a_config["globus_client_id"]

    def on_click_load_config_button_b(self):
        machine_config_file, ok = QFileDialog.getOpenFileName(self, "Open", os.getcwd(), "YAML files (*.yaml *.yml)")
        if not ok:
            return
        with open(machine_config_file, 'r') as f:
            try:
                self.machine_b_config = yaml.safe_load(f)
            except yaml.YAMLError as exc:
                print("Cannot load YAML config for machine a")
                QMessageBox.information(self, "Load Config", "Failed to load config file for machine A", QMessageBox.StandardButton.Close)
                return
        try:
            self.funcx_id_lineedit_b.setText(self.machine_b_config["globus_compute_id"])
            self.globus_id_lineedit_b.setText(self.machine_b_config["globus_transfer_id"])
            self.workdir_lineedit_b.setText(self.machine_b_config["work_dir"])
        except KeyError:
            QMessageBox.warning(self, "Config Error", "Config file not correct!", QMessageBox.StandardButton.Cancel)

        if "defaults" in self.machine_b_config:
            defaults = self.machine_b_config["defaults"]
            if "sz3_exe" in defaults:
                self.sz3_exe_b = defaults["sz3_exe"]
                self.sz3_executable_lineEdit_MB.setText(self.sz3_exe_b)
            if "dataset_dir" in defaults:
                self.dataset_dir_b_default = defaults["dataset_dir"]

        if "globus_client_id" in self.machine_b_config:
            self.globus_client_id = self.machine_b_config["globus_client_id"]

    def on_click_transfer_button_a(self):
        if self.tc is None:
            print("Globus Transfer has not been authenticated!")
            QMessageBox.warning(self, "Authentication Error", "You need to authenticate Globus Transfer first!", QMessageBox.StandardButton.Cancel)
            return

        files_to_transfer :List[Path]= self.listwidget_a_selected_paths

        task_data = globus_sdk.TransferData(
            source_endpoint=self.globus_id_lineedit_a.text(), destination_endpoint=self.globus_id_lineedit_b.text()
        )
        
        for file in files_to_transfer:
            task_data.add_item(
                str(file),  # source
                str(Path(self.workdir_lineedit_b.text()) / file.name),  # dest
            )
            print("transfering ", str(file), " to ", str(Path(self.workdir_lineedit_b.text()) / file.name))
        # submit the task
        transfer_doc_a_to_b = self.tc.submit_transfer(task_data)
        self.transfer_performance_textEdit.clear()
        QMessageBox.information(self, "Transfer", f"The transfer task has been submitted", QMessageBox.StandardButton.Close)

        thread_a = TransferThread(self.tc, transfer_doc_a_to_b)
        thread_a.finished.connect(lambda: (self.check_transfer_status(transfer_doc_a_to_b), thread_a, self.on_click_list_workdir_button_b()))
        thread_a.start()


    def get_html_message(self, message, level:MessageLevel):
        if level == MessageLevel.ALERT:
            html_message = f"{self.alertHTMLTag} {message} {self.endHTMLTag}"
        elif level == MessageLevel.WARNING:
            html_message = f"{self.warningHTMLTag} {message} {self.endHTMLTag}"
        elif level == MessageLevel.SUCCESS:
            html_message = f"{self.successHTMLTag} {message} {self.endHTMLTag}"
        else:
            html_message = f"{self.infoHTMLTag} {message} {self.endHTMLTag}"
        return html_message
    
    def add_message_to_current_status(self, message, level: MessageLevel = MessageLevel.INFO):
        cursor = self.current_status_textEdit.textCursor()
        html_message = self.get_html_message(message, level)
        self.current_status_textEdit.insertHtml(html_message)
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.current_status_textEdit.setTextCursor(cursor)

    def add_message_to_transfer_performance(self, message, level: MessageLevel = MessageLevel.INFO):
        cursor = self.transfer_performance_textEdit.textCursor()
        html_message = self.get_html_message(message, level)
        self.transfer_performance_textEdit.insertHtml(html_message)
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.transfer_performance_textEdit.setTextCursor(cursor)

    def check_transfer_status(self, transfer_doc):
        if transfer_doc is None:
            self.add_message_to_current_status("Error: No transfer task to check!")
            return

        task_id = transfer_doc["task_id"]
        task = self.tc.get_task(task_id)
        print(task)
        status = task['status']
        files = task['files']
        bytes_transferred = task['bytes_transferred']
        request_time = task['request_time']
        completion_time = task['completion_time']
        self.add_message_to_transfer_performance(f"Task {task_id}'s Status: {status}")
        self.add_message_to_transfer_performance("Bytes transferred: " + str(bytes_transferred))
        self.add_message_to_transfer_performance("Request time: " + str(request_time))
        self.add_message_to_transfer_performance("Completion time: " + str(completion_time))
        self.add_message_to_transfer_performance("Files:" + str(files))
        if status == 'ACTIVE':
            self.add_message_to_transfer_performance("Transfer task is running", MessageLevel.INFO)
        elif status == 'SUCCEEDED':
            self.add_message_to_transfer_performance("Transfer task is done", MessageLevel.SUCCESS)

    def on_click_transfer_button_b(self):
        if self.tc is None:
            print("Globus Transfer has not been authenticated!")
            QMessageBox.warning(self, "Authentication Error", "You need to authenticate Globus Transfer first!", QMessageBox.StandardButton.Cancel)
            return

        files_to_transfer :List[Path]= self.listwidget_b_selected_paths

        task_data = globus_sdk.TransferData(
            source_endpoint=self.globus_id_lineedit_b.text(), destination_endpoint=self.globus_id_lineedit_a.text()
        )
        
        for file in files_to_transfer:
            task_data.add_item(
                str(file),  # source
                str(Path(self.workdir_lineedit_a.text()) / file.name),  # dest
            )
            print("transfering ", str(file), " to ", str(Path(self.workdir_lineedit_b.text()) / file.name))
        # submit the task
        transfer_doc_b_to_a = self.tc.submit_transfer(task_data)
        self.transfer_performance_textEdit.clear()
        QMessageBox.information(self, "Transfer", f"The transfer task has been submitted", QMessageBox.StandardButton.Close)

        thread_b = TransferThread(self.tc, transfer_doc_b_to_a)
        thread_b.finished.connect(lambda: (self.check_transfer_status(transfer_doc_b_to_a), thread_b, self.on_click_list_workdir_button_a()))
        thread_b.start()

    def on_click_autotransfer_button_a(self):
        QMessageBox.information(self, "Auto Transfer", "You clicked the Auto Transfer A button!", QMessageBox.StandardButton.Close)

    def on_click_autotransfer_button_b(self):
        QMessageBox.information(self, "Auto Transfer", "You clicked the Auto Transfer B button!", QMessageBox.StandardButton.Close)


if __name__ == '__main__':
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)
    UIWindow = UI()
    sys.exit(app.exec_())