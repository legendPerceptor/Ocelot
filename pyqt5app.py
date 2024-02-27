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

        self.list_workdir_button_a = self.findChild(QPushButton, "list_workdir_button_a")
        self.save_config_button_a = self.findChild(QPushButton, "save_config_button_a")
        self.load_config_button_a = self.findChild(QPushButton, "load_config_button_a")
        self.compress_button_a = self.findChild(QPushButton, "compress_button_a")
        self.decompress_button_a = self.findChild(QPushButton, "decompress_button_a")
        self.transfer_button_a = self.findChild(QPushButton, "transfer_button_a")
        self.auto_transfer_button_a = self.findChild(QPushButton, "auto_transfer_button_a")

        self.workdir_listwidget_a = self.findChild(QListWidget, "workdir_list_widget_b")

        # Machine B Config
        self.funcx_id_lineedit_b = self.findChild(QLineEdit, "funcx_id_lineedit_b")
        self.globus_id_lineedit_b = self.findChild(QLineEdit, "globus_id_lineedit_b")
        self.workdir_lineedit_b = self.findChild(QLineEdit, "workdir_lineedit_b")

        self.list_workdir_button_b = self.findChild(QPushButton, "list_workdir_button_b")
        self.save_config_button_b = self.findChild(QPushButton, "save_config_button_b")
        self.load_config_button_b = self.findChild(QPushButton, "load_config_button_b")
        self.compress_button_b = self.findChild(QPushButton, "compress_button_b")
        self.decompress_button_b = self.findChild(QPushButton, "decompress_button_b")
        self.transfer_button_b = self.findChild(QPushButton, "transfer_button_b")
        self.auto_transfer_button_b = self.findChild(QPushButton, "auto_transfer_button_b")

        self.workdir_listwidget_b = self.findChild(QListWidget, "workdir_listwidget_b")

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
        
        # YAML config information
        self.machine_a_config = None
        self.machine_b_config = None

        self.show()

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
        
        QMessageBox.information(self, "Authenticate", "You have finished Globus Autentication", QMessageBox.StandardButton.Close)

    def on_click_list_workdir_button_a(self):
        QMessageBox.information(self, "List Workdir", "You clicked the List Workdir A button!", QMessageBox.StandardButton.Close)

    def on_click_list_workdir_button_b(self):
        QMessageBox.information(self, "List Workdir", "You clicked the List Workdir B button!", QMessageBox.StandardButton.Close)

    def on_click_save_config_button_a(self):
        QMessageBox.information(self, "Save Config", "You clicked the Save Config A button!", QMessageBox.StandardButton.Close)

    def on_click_save_config_button_b(self):
        QMessageBox.information(self, "Save Config", "You clicked the Save Config B button!", QMessageBox.StandardButton.Close)

    def on_click_load_config_button_a(self):
        machine_config_file, ok = QFileDialog.getOpenFileName(self, "Open", os.getcwd(), "YAML files (*.yaml *.yml)")
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