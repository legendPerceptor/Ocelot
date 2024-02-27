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

from globus_compute_util import list_dir, list_cpu, remove_files

from pathlib import Path

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

        self.show()

    def on_click_register_globus_compute_a(self):
        self.gce_machine_a = Executor(endpoint_id=self.funcx_id_lineedit_a.text().strip(), client=self.gcc)
        future = self.gce_machine_a.submit(list_cpu)
        print("submitted a lscpu to machine A")
        future.add_done_callback(lambda f: print("Machine A CPU Info:\n", f.result()))

    def on_click_register_globus_compute_b(self):
        self.gce_machine_b = Executor(endpoint_id=self.funcx_id_lineedit_b.text().strip(), client=self.gcc)
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
        color_effect = QGraphicsColorizeEffect()
        color_effect.setColor(Qt.GlobalColor.darkGreen) 
        self.authenticate_status_label.setGraphicsEffect(color_effect)

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

    def put_workdir_into_listWidget_b(self, future):
        self.workdir_listwidget_b.clear()
        for file in future.result():
            self.workdir_listwidget_b.addItem(file)

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
        QMessageBox.information(self, "Save Config", "You clicked the Save Config A button!", QMessageBox.StandardButton.Close)

    def on_click_save_config_button_b(self):
        QMessageBox.information(self, "Save Config", "You clicked the Save Config B button!", QMessageBox.StandardButton.Close)

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
        if "globus_client_id" in self.machine_b_config:
            self.globus_client_id = self.machine_b_config["globus_client_id"]

    def on_click_compress_button_a(self):
        QMessageBox.information(self, "Compress", "You clicked the Compress A button!", QMessageBox.StandardButton.Close)

    def on_click_compress_button_b(self):
        QMessageBox.information(self, "Compress", "You clicked the Compress B button!", QMessageBox.StandardButton.Close)

    def on_click_decompress_button_a(self):
        QMessageBox.information(self, "Decompress", "You clicked the Decompress A button!", QMessageBox.StandardButton.Close)

    def on_click_decompress_button_b(self):
        QMessageBox.information(self, "Decompress", "You clicked the Decompress B button!", QMessageBox.StandardButton.Close)

    def on_click_transfer_button_a(self):
        QMessageBox.information(self, "Transfer", "You clicked the Transfer A button!", QMessageBox.StandardButton.Close)

    def on_click_transfer_button_b(self):
        QMessageBox.information(self, "Transfer", "You clicked the Transfer B button!", QMessageBox.StandardButton.Close)

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