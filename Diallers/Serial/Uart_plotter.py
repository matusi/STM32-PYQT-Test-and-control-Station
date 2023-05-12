# -*- coding: utf-8 -*-
import sys
import math
import re
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtSerialPort import QSerialPort, QSerialPortInfo
# from PyQt5.QtCore import  QRect
# from PyQt5.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
#     QGroupBox, QHBoxLayout, QLabel, QPushButton,
#     QSizePolicy, QSpacerItem, QSpinBox, QTextEdit,
#     QVBoxLayout, QWidget)
from pyqtgraph import PlotWidget
import pyqtgraph

import numpy as np
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
import traceback, sys
import time

class WorkerSignals(QObject):

    finished = pyqtSignal()
    error = pyqtSignal(tuple)
    result = pyqtSignal(object)



class ReadPortWorker(QObject):
    """
    Worker class to read data from the serial port
    """
    dataReceived = pyqtSignal(bytes)

    def __init__(self, port, parent=None):
        super().__init__(parent)
        self.port = port

    def run(self):
        while True:
            data = self.port.read(1024)
            if data:
                self.dataReceived.emit(data)


class SendPortWorker(QObject):
    """
    Worker class to send data to the serial port
    """
    def __init__(self, port, data, parent=None):
        super().__init__(parent)
        self.port = port
        self.data = data

    def run(self):
        self.port.write(self.data)


class PlotDataWorker(QObject):
    """
    Worker class to plot data on a graph
    """
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.plotter = SerialDataGraph
    def run(self):
        # Code to plot data on a graph
        self.plotter.appendData()





class MainwindowSerialMonitor(QtWidgets.QMainWindow):
    dataReceived = pyqtSignal(str) # define the dataReceived signal
    def __init__(self, *args, **kwargs):
        super(MainwindowSerialMonitor, self).__init__(*args, **kwargs)
        self.counter = 0
        self.port = QSerialPort()
        self.threadpool = QThreadPool()
        
        self.initUI()
        self.ConnectSignals()
        

    def initUI(self):
        # rest of your code
        self.uartparamsbox = UartParamsQGroupBox(self)
        self.sensorsmanagerbox = SensorsManagerQGroupBox(self)
        self.sensorsplots = SerialDataGraph(self)
    
        self.serialdatasend = SerialDataSend(self)
        
        
        
        ##Main window widdget layout
        self.setCentralWidget(QtWidgets.QWidget(self))
        self.resize(978, 639)
        self.setWindowTitle("UartSensorsDialler")
                ### Status Bar ###
        self.setStatusBar( QtWidgets.QStatusBar(self) )
        self.statusText = QtWidgets.QLabel(self)
        self.statusBar().addWidget( self.statusText )
        
        # Create a QHBoxLayout for the top widgets
        topLayout = QtWidgets.QHBoxLayout()
        topLayout.addWidget(self.uartparamsbox)
        topLayout.addWidget(self.sensorsmanagerbox)
        topLayout.addWidget(self.serialdatasend)
        topLayout.setContentsMargins(3, 3, 3, 3)
        
        # Create a QVBoxLayout for the centralWidget
        centralLayout = QtWidgets.QVBoxLayout(self.centralWidget())
        centralLayout.addLayout(topLayout)
        centralLayout.addWidget(self.sensorsplots)
        centralLayout.setContentsMargins(3, 3, 3, 3)
        
        self.show()
        
        
    def ConnectSignals(self):    
    ### Signal Connect ###
        self.uartparamsbox.UartConnectQButton.clicked.connect(self.portOpen)
        self.serialdatasend.serialSendSignal.connect(self.sendFromPort)
        self.port.readyRead.connect(self.readFromPort)

    def portOpen(self, flag):
        if flag:
            self.port.setBaudRate( self.uartparamsbox.baudRate() )
            self.port.setPortName( self.uartparamsbox.portName() )

            r = self.port.open(QtCore.QIODevice.ReadWrite)
            if not r:
                self.statusText.setText('Port open error')
                self.uartparamsbox.UartConnectQButton.setChecked(False)
                self.uartparamsbox.serialControlEnable(True)
            else:
                self.statusText.setText('Port opened')
                self.uartparamsbox.serialControlEnable(False)
                         # Submit the readFromPort task to the thread pool
                worker = ReadPortWorker(self.port)
                worker.dataReceived.connect(self.dataReceived.emit)
                self.threadpool.start(worker)
        else:
            self.port.close()
            self.statusText.setText('Port closed')
            self.uartparamsbox.serialControlEnable(True)
        
    def readFromPort(self):
        data = self.port.readAll()
        if len(data) > 0:
            self.serialdatamonitor.appendSerialText( QtCore.QTextStream(data).readAll(), QtGui.QColor(255, 0, 0) )

    def sendFromPort(self, text):
        self.port.write( text.encode() )
        self.serialdatamonitor.appendSerialText( text, QtGui.QColor(0, 0, 255) )        
        
   
    
    def slipDecode(self, packet):
        return packet.replace(b'\xDB\xDC', b'\xC0').replace(b'\xDB\xDD', b'\xDB')

    def slipEncode(self, packet):
        return b''.join([ b'\xDB\xDC' if i==192 else b'\xDB\xDD' if i==219 else bytes([i]) for i in packet ]) + b'\xC0'
    

        
        

        
class UartParamsQGroupBox(QtWidgets.QGroupBox):
    
    def __init__(self, parent):
        super(UartParamsQGroupBox, self).__init__(parent)
        self.port = QSerialPort()


        self.UartParamsQGroupBox = QtWidgets.QGroupBox(self)
        self.UartParamsQGroupBox.setObjectName(u"UartParamsQGroupBox")
        self.UartParamsQGroupBox.setGeometry(QRect(50, 0, 50, 50))
        self.UartParamsQGroupBox.setTitle(u"Serial Parameters")
        
        self.UartPortListQComboBox = QtWidgets.QComboBox(self)
        self.UartPortListQComboBox.addItems([ port.portName() for port in QSerialPortInfo().availablePorts() ])

        
        self.UartBaudeRateQCombobox = QtWidgets.QComboBox(self)
        self.UartBaudeRateQCombobox.addItems([
            '110', '300', '600', '1200', '2400', '4800', '9600', '14400', '19200', '28800', 
            '31250', '38400', '51200', '56000', '57600', '76800', '115200', '128000', '230400', '256000', '921600'
        ])
        self.UartBaudeRateQCombobox.setCurrentIndex(16)
        
        self.UartConnectQButton = QtWidgets.QPushButton(self)
        self.UartConnectQButton.setText(u"Connect ")
        self.UartConnectQButton.setCheckable(True)
        
        
        gridLayout = QtWidgets.QGridLayout(self.UartParamsQGroupBox)
        gridLayout.addWidget(self.UartPortListQComboBox)
        gridLayout.addWidget(self.UartBaudeRateQCombobox)
        gridLayout.addWidget(self.UartConnectQButton)
        gridLayout.setColumnStretch(1, 1)
        
        vbox = QtWidgets.QVBoxLayout(self)
        vbox.addWidget(self.UartParamsQGroupBox)
        
    def serialControlEnable(self, flag):
        self.UartBaudeRateQCombobox.setEnabled(flag)
        self.UartPortListQComboBox.setEnabled(flag)
    def baudRate(self):
        return int(self.UartBaudeRateQCombobox.currentText())

    def portName(self):
        return self.UartPortListQComboBox.currentText()
    
    
    
class SensorsManagerQGroupBox(QtWidgets.QGroupBox):
    def __init__(self, parent):
        super(SensorsManagerQGroupBox, self).__init__(parent)

        self.SensorsManagerQGroupBox = QtWidgets.QGroupBox(self)
        self.SensorsManagerQGroupBox.setGeometry(QtCore.QRect(0, 0, 20, 20)) 
        self.SensorsManagerQGroupBox.setTitle("Sensors manager")
        
        self.ADXL355QCheckBox = QtWidgets.QCheckBox(self.SensorsManagerQGroupBox)
        self.ADXL355QCheckBox.setObjectName("Accelerometer")
        self.ADXL355QCheckBox.setText("Accelerometer")
        
        self.ICG20330QCheckBox = QtWidgets.QCheckBox(self.SensorsManagerQGroupBox)
        self.ICG20330QCheckBox.setObjectName("Gyro")
        self.ICG20330QCheckBox.setText("Gyro")
        
    
        
        self.MMCMAQCheckBox = QtWidgets.QCheckBox(self.SensorsManagerQGroupBox)
        self.MMCMAQCheckBox.setObjectName("Magnetometer")
        self.MMCMAQCheckBox.setText("Magnetometer")
        
        self.BSD89QCheckBox = QtWidgets.QCheckBox(self.SensorsManagerQGroupBox)
        self.BSD89QCheckBox.setObjectName("Pressure")
        self.BSD89QCheckBox.setText("Pressure")
        
        
        self.ECSENSORQCheckBox = QtWidgets.QCheckBox(self.SensorsManagerQGroupBox)
        self.ECSENSORQCheckBox.setObjectName("Temperature")
        self.ECSENSORQCheckBox.setText("Temperature")
        
        self.PT1000QCheckBox = QtWidgets.QCheckBox(self.SensorsManagerQGroupBox)
        self.PT1000QCheckBox.setObjectName("Current")
        self.PT1000QCheckBox.setText("Current")
        
        self.VoltageQCheckBox = QtWidgets.QCheckBox(self.SensorsManagerQGroupBox)
        self.VoltageQCheckBox.setObjectName("Voltage")
        self.VoltageQCheckBox.setText("Voltage")
        
        gridLayout = QtWidgets.QGridLayout(self.SensorsManagerQGroupBox)
        gridLayout.addWidget(self.ADXL355QCheckBox, 0, 0)
        gridLayout.addWidget(self.ICG20330QCheckBox, 0, 1)
        gridLayout.addWidget(self.VoltageQCheckBox, 1, 0)
        gridLayout.addWidget(self.MMCMAQCheckBox, 1, 1)
        gridLayout.addWidget(self.BSD89QCheckBox, 2, 0)
        gridLayout.addWidget(self.ECSENSORQCheckBox, 2, 1)
        gridLayout.addWidget(self.PT1000QCheckBox, 3, 0)
        gridLayout.setColumnStretch(1, 1)
        
        vbox = QtWidgets.QVBoxLayout(self)
        vbox.addWidget(self.SensorsManagerQGroupBox)
        

class SerialDataGraph(QtWidgets.QWidget):
    mouseMovedSignal = QtCore.pyqtSignal( float, float, float )
    def __init__(self, parent):
        super(SerialDataGraph, self).__init__(parent)
        
        self.plotWidget = pyqtgraph.PlotWidget()
        self.plotWidget.setBackground('#FFFFFFFF')
        self.plotWidget.plotItem.getAxis('bottom').setPen( pyqtgraph.mkPen(color='#000000') )
        self.plotWidget.plotItem.getAxis('left').setPen( pyqtgraph.mkPen(color='#000000') )
        self.plotWidget.plotItem.showGrid(True, True, 0.3)
        self.plotWidget.setXRange(0, 300)

        self.data = [ self.plotWidget.plotItem.plot(pen='r'), self.plotWidget.plotItem.plot(pen='b')]
        self.data[0].setData( np.zeros(300) )
        self.data[1].setData( np.zeros(300) )

        self.crossHairV = pyqtgraph.InfiniteLine(angle=90, movable=False)
        self.crossHairH = pyqtgraph.InfiniteLine(angle=0, movable=False)
        self.plotWidget.addItem(self.crossHairV, ignoreBounds=True)
        self.plotWidget.addItem(self.crossHairH, ignoreBounds=True)
        self.plotWidget.scene().sigMouseMoved.connect(self.mouseMovedEvent)

        self.setLayout( QtWidgets.QVBoxLayout() )
        self.layout().addWidget(self.plotWidget)

    def appendData(self, data, yNum):
        rolled = np.roll(self.data[yNum].yData, -1)
        rolled[-1] = data
        self.data[yNum].setData(rolled)

    def mouseMovedEvent(self, pos):
        if self.plotWidget.sceneBoundingRect().contains(pos):
            mousePoint = self.plotWidget.plotItem.getViewBox().mapSceneToView(pos)
            index = int( mousePoint.x() )
            data0, data1 = self.data[0].yData, self.data[1].yData
            if 0 <= index < data0.shape[0] and 0 <= index < data1.shape[0]:
                self.mouseMovedSignal.emit( mousePoint.x(), data0[index], data1[index] )
            self.crossHairV.setPos( mousePoint.x() )
            self.crossHairH.setPos( mousePoint.y() )
            

class SerialDataSend(QtWidgets.QWidget):

    serialSendSignal = QtCore.pyqtSignal(str)

    def __init__(self, parent):
        super(SerialDataSend, self).__init__(parent)

        self.sendData = QtWidgets.QTextEdit(self)
        self.sendData.setAcceptRichText(False)

        self.sendButton = QtWidgets.QPushButton('Send')
        self.sendButton.resize(4,4)
        
        self.setLayout( QtWidgets.QVBoxLayout(self) )
        self.layout().addWidget(self.sendData)
        self.layout().addWidget(self.sendButton)
        self.layout().setContentsMargins(3, 3, 3, 3)
    def sendButtonClicked(self):
        self.serialSendSignal.emit( self.sendData.toPlainText() )
        self.sendData.clear()
                
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainwindowSerialMonitor()
    
    app.exec()