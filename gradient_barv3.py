import sys
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5 import QtGui, QtCore

from matplotlib import pyplot as plt
from pydantic import BaseModel


class Marker:
    def __init__(self, pos, eb, color = None):
        self.pos = pos
        self.eb = eb
        self.color = color

    def __str__(self):
        return f"Marker(pos: {self.pos}, eb: {self.eb}, color:{self.color})"

def getColorAtPosition(gradient: QLinearGradient, position: float) -> QColor:
    stops = gradient.stops()
    if not stops:
        return QColor()  # Return a default QColor if there are no stops

    # Ensure position is within bounds
    position = max(0.0, min(position, 1.0))

    colorBefore = stops[0][1]
    colorAfter = stops[-1][1]

    for i in range(len(stops)):
        if stops[i][0] > position:
            if i > 0:
                posBefore, colorBefore = stops[i-1]
                posAfter, colorAfter = stops[i]

                ratio = (position - posBefore) / (posAfter - posBefore)
                return QColor.fromRgbF(
                    colorBefore.redF() + ratio * (colorAfter.redF() - colorBefore.redF()),
                    colorBefore.greenF() + ratio * (colorAfter.greenF() - colorBefore.greenF()),
                    colorBefore.blueF() + ratio * (colorAfter.blueF() - colorBefore.blueF()),
                    colorBefore.alphaF() + ratio * (colorAfter.alphaF() - colorBefore.alphaF())
                )
            break

    # If the position matches the last stop or beyond, return the last color
    return colorAfter

class GradientBar(QWidget):
    def __init__(self, cmap = None):
        super().__init__()
        self.markers = []  # Example markers
        self.dragging_marker_index = None
        self.setLayout(QVBoxLayout())
        # self.setMinimumHeight(100)
        self.setMinimumWidth(30)
        self.cmap = cmap
        self.data_min = None
        self.data_max = None
        self.show_tick_marks = True
        # Draw gradient
        self.updateGradient()

    def getMarkers(self) -> list[Marker]:
        return self.markers

    def updateGradient(self):
        self.gradient = QLinearGradient(0, 0, 0, self.height())
        if self.cmap is not None:
            for i in range(self.cmap.N):
                color = self.cmap(i)
                color = QColor(int(color[0]*255), int(color[1]*255), int(color[2]*255))
                pos = i / self.cmap.N
                self.gradient.setColorAt(pos, color)
        else:
            for marker in self.markers:
                self.gradient.setColorAt(marker.pos, marker.color)

    def resizeEvent(self, a0: QResizeEvent | None) -> None:
        super().resizeEvent(a0)
        self.updateGradient()

    def toggleTickMark(self, show_tick_marks: bool):
        self.show_tick_marks = show_tick_marks
        self.update()

    def setDataRange(self, data_min, data_max):
        self.data_min = data_min
        self.data_max = data_max

    def showContextMenu(self, position, marker_index):
        contextMenu = QMenu(self)
        changeColorAction = contextMenu.addAction("Change Setting")
        removeMarkerAction = contextMenu.addAction("Remove Marker")

        action = contextMenu.exec_(self.mapToGlobal(position))
        if action == changeColorAction:
            self.changeMarkerSetting(marker_index)
        elif action == removeMarkerAction:
            self.removeMarker(marker_index)

    def changeMarkerSetting(self, marker_index):
        marker = self.markers[marker_index]
        # new_color = QColorDialog.getColor(color, self)
        new_eb, ok = QInputDialog.getDouble(self, "New Error Bound", "eb", value=marker.eb, min=-1000, max=1000, decimals=10)
        if ok:
            marker.eb = new_eb
            self.update()

    def removeMarker(self, marker_index):
        if len(self.markers) > 1:  # Prevent removing all markers
            del self.markers[marker_index]
            self.update()
        else:
            QMessageBox.information(self, "Action Denied", "At least one marker is required.")


    def mousePressEvent(self, event):
        # Determine if a marker was clicked
        for index, marker in enumerate(self.markers):
            marker_rect = self.markerRect(marker.pos)
            if marker_rect.contains(event.pos()):
                if event.button() == Qt.RightButton:
                    # Change color
                    self.showContextMenu(event.pos(), index)
                self.dragging_marker_index = index
                return
        # not clicking a marker
        if event.button() == Qt.RightButton:
            # add a new marker
            pos = event.pos().y() / self.height()
            eb, ok = QInputDialog.getDouble(self, "New Error Bound", "eb", value=0.01, min=-1000, max=1000, decimals=10)
            color = getColorAtPosition(self.gradient, pos)
            if ok:
                self.markers.append(Marker(pos, eb, color))
                self.markers.sort(key=lambda m:m.pos)  # Ensure markers are sorted by position
                self.update()

        self.dragging_marker_index = None

    def mouseMoveEvent(self, event):
        if self.dragging_marker_index is not None and event.buttons() == Qt.LeftButton:
            new_pos = event.pos().y() / self.height()
            new_pos = max(0, min(new_pos, 1))  # Constrain within [0, 1]
            marker = self.markers[self.dragging_marker_index]
            marker.pos = new_pos
            marker.color = getColorAtPosition(self.gradient, marker.pos)
            self.update()

    def mouseReleaseEvent(self, event):
        if self.dragging_marker_index is not None:
            self.dragging_marker_index = None

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.fillRect(self.rect(), self.gradient)

        painter.setPen(QPen(Qt.white, 2)) 
        # Draw Ticks
        if self.show_tick_marks:
            self.drawTicks(painter)

        # Draw markers
        for marker in self.markers:
            painter.setBrush(QBrush(marker.color))
            marker_rect = self.markerRect(marker.pos)
            painter.drawRect(marker_rect)

        
    
    def drawTicks(self, painter):
        tickCount = 10  # Number of ticks
        interval = self.height() / (tickCount - 1)
        # painter.setPen(QPen(Qt.white, 2))  # Set the color and width of ticks

        for i in range(tickCount):
            y = interval * i
            tickLength = 10 if i % 5 == 0 else 5  # Longer ticks every 5th tick
            painter.drawLine(self.width() - tickLength, int(y), self.width(), int(y))

            # if i % 5 == 0:  # Add labels for every 5th tick
            
            label = f"{1 - i / (tickCount - 1):.1f}"  # Calculate the label value (reverse order)
            if self.data_min is not None and self.data_max is not None:
                percent = 1 - i / (tickCount - 1)
                value = (self.data_max - self.data_min) * percent + self.data_min
                label = f"{value:.1f}"
            painter.setFont(QFont("Arial", 8))
            painter.drawText(self.width() - tickLength - 15, int(y) + 4, label)

    def markerRect(self, pos):
        # marker_width = 10
        # marker_height = 20
        # x = pos * self.width() - marker_width / 2
        # y = self.height() - marker_height  # Adjust this to place markers at desired edge
        # return QRectF(x, y, marker_width, marker_height)
        marker_width = 20  # Adjusted for vertical layout
        marker_height = 10
        x = self.width() - marker_width  # Position at the right edge
        y = pos * self.height() - marker_height / 2
        return QRectF(x, y, marker_width, marker_height)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = GradientBar(plt.get_cmap('rainbow'))
    w.resize(100, 400)
    w.show()
    sys.exit(app.exec_())
