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

class DataRect(BaseModel):
    start_x: int = 0
    start_y: int = 0
    end_x: int = 0
    end_y: int = 0
    length_x: int = 0
    length_y: int = 0

def _getData(dimension: List[int]):
    data_file = "./data/CLDHGH_1_1800_3600.dat"
    with open(data_file, 'rb') as f:
        data = np.fromfile(f,dtype=np.float32)
        data = np.reshape(data, dimension)

    fig = Figure(dpi=100)
    canvas = FigureCanvas(fig)
    fig.subplots_adjust(bottom=0, top=1, left=0, right=1)
    ax = fig.add_subplot(111)
    data_min, data_max = np.min(data), np.max(data)
    # ax.set_in_layout(False)
    ax.imshow(data, cmap=plt.get_cmap('rainbow').reversed(), norm=plt.Normalize(vmin=data_min, vmax=data_max), aspect='auto')
    # fig.tight_layout(pad=0)
    canvas.draw()
    width, height = canvas.get_width_height()
    img = QImage(canvas.buffer_rgba(), width, height, QImage.Format_RGB32)

    return (img, data_min, data_max)


class ImageLabel(QLabel):
    def __init__(self, dim_x = None, dim_y = None):
        super().__init__()
        # self.setMinimumWidth(100)
        # self.setMinimumHeight(100)
        self.currentImage = None
        self.startPoint = self.endPoint = None
        self.rect = QRect()
        self.dim_x = dim_x
        self.dim_y = dim_y
        self.show_tick_marks = True
    
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
            self.update()

    def mouseMoveEvent(self, event):
        if event.buttons() & Qt.LeftButton and self.currentImage:
            self.endPoint = event.pos()
            self.update()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.currentImage:
            self.endPoint = event.pos()
            self.printRect()
            self.convertMousePositionToData(self.startPoint, self.endPoint)
            self.update()
    
    def convertMousePositionToData(self, startPos, endPos):
        print("start pos:",startPos.x(), startPos.y())
        print("end pos:", endPos)
        dataRect = DataRect()
        dataRect.start_x = int(startPos.x() / self.width() * self.dim_x)
        dataRect.start_y = int(startPos.y() / self.height() * self.dim_y)
        dataRect.end_x = int(endPos.x() / self.width() * self.dim_x)
        dataRect.end_y = int(endPos.y() / self.height() * self.dim_y)
        dataRect.length_x = dataRect.end_x - dataRect.start_x
        dataRect.length_y = dataRect.end_y - dataRect.start_y
        print(dataRect)
    
    def printRect(self):
        if not self.currentImage:
            return
        # Calculate the average color in the selected rectangle
        rect = QRect(self.startPoint, self.endPoint).normalized()
        print(rect)

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        if self.startPoint and self.endPoint:
            rect = QRect(self.startPoint, self.endPoint)
            painter.setPen(QColor(255, 0, 0))
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
    def __init__(self, window_title = 'Image Loader with Rectangle Draw and Color Bar'):
        super().__init__()
       
        self.colorBar = GradientBar(cmap=plt.get_cmap('rainbow').reversed())
        self.maxImageWidth = 600  # Maximum width for the image
        self.maxImageHeight = 400  # Maximum height for the image
        
        # temporary fake data
        self.dataDimension = [1800, 3600]
        self.imageLabel = ImageLabel()
        self.imageLabel.setDimension(self.dataDimension)

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
        containerLayout.addWidget(self.loadImageButton)

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

    def loadImage(self):
        img, data_min, data_max = _getData(self.dataDimension) 
        self.colorBar.setDataRange(data_min, data_max)
        pixmap = QPixmap.fromImage(img)
        self.imageLabel.setPixmap(pixmap)
        self.imageLabel.currentImage = pixmap.toImage()
        self.update()
        # imagePath, _ = QFileDialog.getOpenFileName()
        # if imagePath:

        #     pixmap = QPixmap(imagePath)
            
        #     # Resize the image if it's larger than the maximum dimensions
        #     pixmap = pixmap.scaled(self.maxImageWidth, self.maxImageHeight, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            
        #     self.imageLabel.setPixmap(pixmap)
        #     self.imageLabel.currentImage = pixmap.toImage()
        #     self.update()

if __name__ == '__main__':
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
    app = QApplication(sys.argv)
    ex = ImageDialog()
    ex.show()
    sys.exit(app.exec_())
