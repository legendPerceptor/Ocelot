import sys
import os
from PyQt5.QtGui import QPaintEvent
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtGui, QtCore

from gradient_barv3 import GradientBar
import matplotlib.colors as colors
from matplotlib import pyplot as plt
import numpy as np

from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from typing import List

from pydantic import BaseModel

import random

from globus_compute_util import get_preview_data

def generate_random_color_hex():
    """Generate a random color in hexadecimal format."""
    return "#{:06x}".format(random.randint(0, 0xFFFFFF))

class DataRect(BaseModel):
    start_x: int = 0
    start_y: int = 0
    end_x: int = 0
    end_y: int = 0
    length_x: int = 0
    length_y: int = 0


class ImageLabel(QLabel):
    def __init__(self, dim_x = None, dim_y = None):
        super().__init__()
        # self.setMinimumWidth(100)
        # self.setMinimumHeight(100)
        self.currentImage = None
        self.startPoint = self.endPoint = None
        self.dim_x = dim_x
        self.dim_y = dim_y
        self.show_tick_marks = True
        self.rects = [] # each is a tuple of QRect and dataRect
        self.previewRect = False
        self.colors = ["#e74c3c", "#f1c40f", "#2980b9", "#8e44ad", "#2c3e50"]
        self.pen = QPen(Qt.GlobalColor.red, 1)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def getRects(self):
        return self.rects

    def toggleTickMark(self, show_tick_marks: bool):
        self.show_tick_marks = show_tick_marks
        self.update()
    
    def setDimension(self, dimension: List[int]):
        self.dim_y = dimension[0]
        self.dim_x = dimension[1]

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.currentImage:
            # Adjust for the position of the imageLabel
            self.startPoint = event.pos()
            self.endPoint = self.startPoint
            self.previewRect = True
            self.update()

    def keyPressEvent(self, ev: QKeyEvent | None) -> None:
        if ev.key() == Qt.Key_Z and (ev.modifiers() & Qt.ControlModifier):
            if len(self.rects) > 0:
                self.rects.pop()
                self.update()

        elif ev.modifiers() & Qt.ControlModifier:
            self.pen = QPen()
            self.pen.setColor(Qt.GlobalColor.green)
            self.pen.setWidth(3)
            self.update()
        
    def keyReleaseEvent(self, a0: QKeyEvent | None) -> None:
        if a0.key() == Qt.Key_Control:
            self.pen = QPen()
            self.pen.setColor(Qt.GlobalColor.red)
            self.pen.setWidth(1)
            self.update()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.currentImage:
            self.endPoint = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.currentImage:
            self.endPoint = event.pos()
            self.previewRect = False
            self.printRect()    
            if len(self.rects) == 0 or event.modifiers() == Qt.ControlModifier:
                rect = QRect(self.startPoint, self.endPoint).normalized()
                curDataRect = self.convertMousePositionToData(self.startPoint, self.endPoint)
                if len(self.rects) < len(self.colors):
                    color = QColor(self.colors[len(self.rects)])
                else:
                    color = QColor(generate_random_color_hex())
                self.rects.append((rect, curDataRect, color))
            elif len(self.rects) == 1: # update the existing
                rect = QRect(self.startPoint, self.endPoint).normalized()
                curDataRect = self.convertMousePositionToData(self.startPoint, self.endPoint)
                self.rects[0] = (rect, curDataRect, QColor(self.colors[0]))

            self.update()
    
    def convertMousePositionToData(self, startPos, endPos):
        dataRect = DataRect()
        dataRect.start_x = int(startPos.x() / self.width() * self.dim_x)
        dataRect.start_y = int(startPos.y() / self.height() * self.dim_y)
        dataRect.end_x = int(endPos.x() / self.width() * self.dim_x)
        dataRect.end_y = int(endPos.y() / self.height() * self.dim_y)
        dataRect.length_x = dataRect.end_x - dataRect.start_x
        dataRect.length_y = dataRect.end_y - dataRect.start_y
        print(dataRect)
        return dataRect
    
    def printRect(self):
        if not self.currentImage:
            return
        # Calculate the average color in the selected rectangle
        rect = QRect(self.startPoint, self.endPoint).normalized()
        print(rect)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        if self.startPoint and self.endPoint and self.previewRect:
            rect = QRect(self.startPoint, self.endPoint)
            painter.setPen(self.pen)
            painter.drawRect(rect)

        # draw existing rects
        for (rect, _, color) in self.rects:
            pen = QPen(color)
            painter.setPen(pen)
            painter.drawRect(rect)
        
        # draw ticks and marks
        if self.show_tick_marks and self.dim_x is not None and self.dim_y is not None:
            self.drawTicks(painter)    

    def drawTicks(self, painter):
        tickCount = 10  # Number of ticks
        interval_y = self.height() / (tickCount - 1)
        interval_x = self.width() / (tickCount - 1)
        painter.setPen(QPen(Qt.white, 2))  # Set the color and width of ticks

        for i in range(tickCount):
            y = int(interval_y * i)
            tickLength = 10 if i % 5 == 0 else 5  # Longer ticks every 5th tick
            painter.drawLine(0, y, tickLength, y)
            
            label = f"{1 - i / (tickCount - 1):.1f}"  # Calculate the label value (reverse order)
            if self.dim_y is not None:
                percent = i / (tickCount - 1)
                value = int(self.dim_y * percent)
                label = str(value)
            painter.setFont(QFont("Arial", 8))
            painter.drawText(15, y + 4, label)

            x = int(interval_x * i)
            painter.drawLine(x, self.height(), x, self.height() - tickLength)
            if self.dim_x is not None:
                percent = i / (tickCount - 1)
                value = int(self.dim_x * percent)
                label = str(value)
            painter.setFont(QFont("Arial", 8))
            painter.drawText(x - 4, self.height() - 15, label)

class ImageDialog(QDialog):
    def __init__(self, window_title = 'Image Loader with Rectangle Draw and Color Bar',
                 gce = None, file_path = "./data/CLDHGH_1_1800_3600.dat", dataDimension = "1800 3600"):
        super().__init__()
       
        self.colorBar = GradientBar(cmap=plt.get_cmap('rainbow').reversed())
        self.maxImageWidth = 600  # Maximum width for the image
        self.maxImageHeight = 400  # Maximum height for the image
        
        self.dimension = [int(dim) for dim in dataDimension.split()]
        # temporary fake data
        self.imageLabel = ImageLabel()
        self.imageLabel.setDimension(self.dimension)
        
        self.gce = gce
        self.file_path = file_path
        self.dataDimensionTxt = dataDimension

        # init UI
        self.initUI(window_title)
    
    def toggleTickMark(self):
        flag = self.toggle_tick_mark_checkbox.isChecked()
        self.imageLabel.toggleTickMark(flag)
        self.colorBar.toggleTickMark(flag)

    def initUI(self, window_title):
        self.setWindowTitle(window_title)
        # self.setGeometry(100, 100, 1000, 600)

        mainLayout = QHBoxLayout()

        # Container for the load button and image display
        containerLayout = QVBoxLayout()
        self.loadImageButton = QPushButton('Load Data')
        self.loadImageButton.clicked.connect(self.loadImage)
        self.accept_button = QPushButton('Accept')
        self.accept_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton('Cancel')
        self.cancel_button.clicked.connect(self.reject)

        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.loadImageButton)
        buttonLayout.addWidget(self.accept_button)
        buttonLayout.addWidget(self.cancel_button)

        containerLayout.addLayout(buttonLayout)

        self.toggle_tick_mark_checkbox = QCheckBox('show ticks and marks')
        self.toggle_tick_mark_checkbox.setChecked(True)
        self.toggle_tick_mark_checkbox.clicked.connect(self.toggleTickMark)
        containerLayout.addWidget(self.toggle_tick_mark_checkbox)
        # Limit the button height
        self.loadImageButton.setMaximumHeight(40)

        containerLayout.addWidget(self.imageLabel)
        mainLayout.addLayout(containerLayout)

        # Add the color bar to the main layout
        mainLayout.addWidget(self.colorBar)

        self.setLayout(mainLayout)

    def getRects(self):
        return self.imageLabel.getRects()

    def image_loaded_callback(self, buf, data_min, data_max):
        qimage = QImage()
        qimage.loadFromData(buf.getvalue(), 'PNG')
        self.colorBar.setDataRange(data_min, data_max)
        pixmap = QPixmap.fromImage(qimage)
        self.imageLabel.setPixmap(pixmap)
        self.imageLabel.currentImage = pixmap.toImage()
        self.update()

    def loadImage(self):
        if self.gce == None:
            img, data_min, data_max = get_preview_data(self.dataDimensionTxt, self.file_path)
            self.image_loaded_callback(img, data_min, data_max)
        else:
            future = self.gce.submit(get_preview_data, self.dataDimensionTxt, self.file_path)
            future.add_done_callback(lambda f: self.image_loaded_callback(*f.result()))
        

if __name__ == '__main__':
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    ex = ImageDialog()
    ex.show()
    sys.exit(app.exec_())
