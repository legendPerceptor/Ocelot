import sys
from PyQt5 import QtWidgets, uic

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5 import QtGui, QtCore

import os
import globus_utils
import globus_sdk

class UI(QDialog):
    def __init__(self):
        super(UI, self).__init__()
        uic.loadUi("ocelot.ui", self)

        self.globus_client_id = "1fb9c8a9-1aff-4d46-9f37-e3b0d44194f2"

        # Machine A Config
        self.funcx_id_lineedit_a = self.findChild(QLineEdit, "funcx_id_lineedit_a")
        self.globus_id_lineedit_a = self.findChild(QLineEdit, "globus_id_lineedit_a")
        self.workdir_lineedit_a = self.findChild(QLineEdit, "workdir_lineedit_a")

        self.authenticate_button_a = self.findChild(QPushButton, "authenticate_button_a")
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

        self.authenticate_button_b = self.findChild(QPushButton, "authenticate_button_b")
        self.list_workdir_button_b = self.findChild(QPushButton, "list_workdir_button_b")
        self.save_config_button_b = self.findChild(QPushButton, "save_config_button_b")
        self.load_config_button_b = self.findChild(QPushButton, "load_config_button_b")
        self.compress_button_b = self.findChild(QPushButton, "compress_button_b")
        self.decompress_button_b = self.findChild(QPushButton, "decompress_button_b")
        self.transfer_button_b = self.findChild(QPushButton, "transfer_button_b")
        self.auto_transfer_button_b = self.findChild(QPushButton, "auto_transfer_button_b")

        self.workdir_listwidget_b = self.findChild(QListWidget, "workdir_listwidget_b")

        # Button Callback Connection
        self.authenticate_button_a.clicked.connect(self.on_click_authenticate_button_a)
        self.list_workdir_button_a.clicked.connect(self.on_click_list_workdir_button_a)
        self.save_config_button_a.clicked.connect(self.on_click_save_config_button_a)
        self.load_config_button_a.clicked.connect(self.on_click_load_config_button_a)
        self.compress_button_a.clicked.connect(self.on_click_compress_button_a)
        self.decompress_button_a.clicked.connect(self.on_click_decompress_button_a)
        self.transfer_button_a.clicked.connect(self.on_click_transfer_button_a)
        self.auto_transfer_button_a.clicked.connect(self.on_click_autotransfer_button_a)

        self.authenticate_button_b.clicked.connect(self.on_click_authenticate_button_b)
        self.list_workdir_button_b.clicked.connect(self.on_click_list_workdir_button_b)
        self.save_config_button_b.clicked.connect(self.on_click_save_config_button_b)
        self.load_config_button_b.clicked.connect(self.on_click_load_config_button_b)
        self.compress_button_b.clicked.connect(self.on_click_compress_button_b)
        self.decompress_button_b.clicked.connect(self.on_click_decompress_button_b)
        self.transfer_button_b.clicked.connect(self.on_click_transfer_button_b)
        self.auto_transfer_button_b.clicked.connect(self.on_click_autotransfer_button_b)
        
        self.show()

    def on_click_authenticate_button_a(self):
        collections = [self.globus_id_lineedit_a.text().strip()]
        cwd = os.getcwd()
        globus_client_id = self.globus_client_id 
        print('globus client id:',globus_client_id)
        try:
            self.globus_authorizer = globus_utils.get_proxystore_authorizer(globus_client_id, self.globus_token_filename, cwd)
            # self.globus_authorizer = globus_utils.get_one_time_authorizer(globus_client_id, collections=collections)
            self.tc = globus_sdk.TransferClient(authorizer=self.globus_authorizer)
        except globus_utils.GlobusAuthFileError:
            print(
                'Performing authentication for the ProxyStore Globus Native app.',
            )
            globus_utils.proxystore_authenticate(
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
                'delete your tokens (proxystore-globus-auth --delete) and try '
                'again.',
            )
        self.status.set("Globus Auth Done")
        self.status_label.configure(foreground='green')
        
        QMessageBox.information(self, "Authenticate", "You clicked the authenticate A button!", QMessageBox.StandardButton.Close)


    def on_click_authenticate_button_b(self):
        QMessageBox.information(self, "Authenticate", "You clicked the authenticate B button!", QMessageBox.StandardButton.Close)

    def on_click_list_workdir_button_a(self):
        QMessageBox.information(self, "List Workdir", "You clicked the List Workdir A button!", QMessageBox.StandardButton.Close)

    def on_click_list_workdir_button_b(self):
        QMessageBox.information(self, "List Workdir", "You clicked the List Workdir B button!", QMessageBox.StandardButton.Close)

    def on_click_save_config_button_a(self):
        QMessageBox.information(self, "Save Config", "You clicked the Save Config A button!", QMessageBox.StandardButton.Close)

    def on_click_save_config_button_b(self):
        QMessageBox.information(self, "Save Config", "You clicked the Save Config B button!", QMessageBox.StandardButton.Close)

    def on_click_load_config_button_a(self):
        QMessageBox.information(self, "Load Config", "You clicked the Load Config A button!", QMessageBox.StandardButton.Close)

    def on_click_load_config_button_b(self):
        QMessageBox.information(self, "Load Config", "You clicked the Load Config B button!", QMessageBox.StandardButton.Close)

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




app = QtWidgets.QApplication(sys.argv)

UIWindow = UI()

sys.exit(app.exec_())