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


# class PlotDataWorker(QObject):
#     """
#     Worker class to plot data on a graph
#     """
#     def __init__(self, data, parent=None):
#         super().__init__(parent)
#         self.data = data
#        # self.plotter = SerialDataGraph
#     def run(self):
#         # Code to plot data on a graph
#         self.plotter.appendData()


class DisplayDataWorker(QObject):
    """
    Worker class to display data in a text box
    """
    def __init__(self, data, parent=None):
        super().__init__(parent)
        self.data = data
        self.monitor= SerialDataMonitor()

    def run(self):
        # Code to display data in a text box

        self.monitor.appendSerialText()




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
        self.serialdatamonitor =SerialDataMonitor(self)
        self.serialdatasend = SerialDataSend(self)
        self.dataflowmanagerbox = DataFlowManagerQGroupBox(self)
        
        self.PacketsManager=  DataPacketsManagerQGroupBox (self)
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
        topLayout.addWidget(self.dataflowmanagerbox)
        
        topLayout.addWidget(self.PacketsManager)
        # topLayout.addWidget(self.serialdatamonitor)
        # topLayout.addWidget(self.serialdatasend)
        topLayout.setContentsMargins(3, 3, 3, 3)
        
        # Create a QVBoxLayout for the centralWidget
        centralLayout = QtWidgets.QVBoxLayout(self.centralWidget())
        centralLayout.addWidget(self.serialdatamonitor)
        centralLayout.addWidget(self.serialdatasend)
        centralLayout.addLayout(topLayout)
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
    
    
    

        

            
class SerialDataMonitor(QtWidgets.QWidget):
    def __init__(self, parent):
        super(SerialDataMonitor, self).__init__(parent)
        self.serialData = QtWidgets.QTextEdit(self)
        self.serialData.setReadOnly(True)
        self.serialData.setFontFamily('Courier New')

        self.serialDataHex = QtWidgets.QTextEdit(self)
        self.serialDataHex.setReadOnly(True)
        self.serialDataHex.setFontFamily('Courier New')

        self.label = QtWidgets.QLabel('00 01 02 03 04 05 06 07 08 09 0A 0B 0C 0D 0E 0F')
        self.label.setFont( QtGui.QFont('Courier New') )
        self.label.setIndent(5)

        self.setLayout( QtWidgets.QGridLayout(self) )
        self.layout().addWidget(self.serialData,    0, 0, 2, 1)
        self.layout().addWidget(self.label,         0, 1, 1, 1)
        self.layout().addWidget(self.serialDataHex, 1, 1, 1, 1)
        self.layout().setContentsMargins(2, 2, 2, 2)
        
        
    def appendSerialText(self, appendText, color):
        self.serialData.moveCursor(QtGui.QTextCursor.End)
        self.serialData.setFontFamily('Courier New')
        self.serialData.setTextColor(color)
        self.serialDataHex.moveCursor(QtGui.QTextCursor.End)
        self.serialDataHex.setFontFamily('Courier New')
        self.serialDataHex.setTextColor(color)

        self.serialData.insertPlainText(appendText)
        
        lastData = self.serialDataHex.toPlainText().split('\n')[-1]
        lastLength = math.ceil( len(lastData) / 3 )
        
        appendLists = []
        splitedByTwoChar = re.split( '(..)', appendText.encode().hex() )[1::2]
        if lastLength > 0:
            t = splitedByTwoChar[ : 16-lastLength ] + ['\n']
            appendLists.append( ' '.join(t) )
            splitedByTwoChar = splitedByTwoChar[ 16-lastLength : ]

        appendLists += [ ' '.join(splitedByTwoChar[ i*16 : (i+1)*16 ] + ['\n']) for i in range( math.ceil(len(splitedByTwoChar)/16) ) ]
        if len(appendLists[-1]) < 47:
            appendLists[-1] = appendLists[-1][:-1]

        for insertText in appendLists:
            self.serialDataHex.insertPlainText(insertText)
        
        self.serialData.moveCursor(QtGui.QTextCursor.End)
        self.serialDataHex.moveCursor(QtGui.QTextCursor.End) 
        
        
        
        
        
#### Serial Data send         
        
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
     
     
     
     
     
## DATA DIRECTION MANAGER
     
        
class DataFlowManagerQGroupBox(QtWidgets.QGroupBox):
    def __init__(self, parent):
        super(DataFlowManagerQGroupBox, self).__init__(parent)

        self.DataFlowManagerQGroupBox = QtWidgets.QGroupBox(self)
        self.DataFlowManagerQGroupBox.setGeometry(QtCore.QRect(0, 0, 5, 5)) 
        self.DataFlowManagerQGroupBox.setTitle("Data flow manager")
        
        self.SendQCheckBox = QtWidgets.QCheckBox(self.DataFlowManagerQGroupBox)
        self.SendQCheckBox.setObjectName("Send")
        self.SendQCheckBox.setText("Send")
        
        self.ReceiveQCheckBox = QtWidgets.QCheckBox(self.DataFlowManagerQGroupBox)
        self.ReceiveQCheckBox.setObjectName("Receive")
        self.ReceiveQCheckBox.setText("Receive")
        
        
        
        gridLayout = QtWidgets.QGridLayout(self.DataFlowManagerQGroupBox)
        gridLayout.addWidget(self.SendQCheckBox, 0, 0)
        gridLayout.addWidget(self.ReceiveQCheckBox, 1, 0)
        gridLayout.setColumnStretch(1, 1)
        
        vbox = QtWidgets.QVBoxLayout(self)
        vbox.addWidget(self.DataFlowManagerQGroupBox)
        
        
        
        
### DATA PACKETS MANAGER  HEX / BIN / ASCI  DELIMITER        
        
class DataPacketsManagerQGroupBox(QtWidgets.QGroupBox):
    
    def __init__(self, parent):
        super(DataPacketsManagerQGroupBox, self).__init__(parent)
        self.port = QSerialPort()


        self.DataPacketsManagerQGroupBox = QtWidgets.QGroupBox(self)
        self.DataPacketsManagerQGroupBox.setObjectName(u"DataPacketsManagerQGroupBox")
        self.DataPacketsManagerQGroupBox.setGeometry(QRect(50, 0, 50, 50))
        self.DataPacketsManagerQGroupBox.setTitle(u"Data packets manager")
        
        
        self.DataPacketsQCombobox = QtWidgets.QComboBox(self)
        self.DataPacketsQCombobox.addItems([
            'HEX', 'ASCI', 'BIN'
        ])
        
        self.DataPacketsQCombobox.setCurrentIndex(1)
        
        
        
        self.DelimiterQCombobox = QtWidgets.QComboBox(self)
        self.DelimiterQCombobox.addItems([
            '\n', '#'
        ])
        self.DelimiterQCombobox.setCurrentIndex(1)
        
    
        
        
        gridLayout = QtWidgets.QGridLayout(self.DataPacketsManagerQGroupBox)
        gridLayout.addWidget(self.DataPacketsQCombobox)
        gridLayout.addWidget(self.DelimiterQCombobox)
        gridLayout.setColumnStretch(1, 1)
        
        vbox = QtWidgets.QVBoxLayout(self)
        vbox.addWidget(self.DataPacketsManagerQGroupBox)
        
    def serialControlEnable(self, flag):
        self.DataPacketsQCombobox.setEnabled(flag)
        self.DelimiterQCombobox.setEnabled(flag)
    def DataPacket(self):
        return int(self.DataPacketsQCombobox.currentText())

    def Delimiter(self):
        return self.DelimiterQCombobox.currentText()
                
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainwindowSerialMonitor()
    
    app.exec()
    
    
