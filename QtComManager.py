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
import traceback
import time




class MainwindowSerialMonitor(QtWidgets.QMainWindow):
    dataReceived = pyqtSignal(str) # define the dataReceived signal
    def __init__(self, *args, **kwargs):
        super(MainwindowSerialMonitor, self).__init__(*args, **kwargs)
        self.counter = 0
        self.port = QSerialPort()
        self.threadpool = QThreadPool()
        
        self.initUI()
    
        

    def initUI(self):
        
        
        
        # Widgets initialisation
        self.uartparamsbox = UartParamsQGroupBox(self)
   
        
        
        
        
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
        
        topLayout.setContentsMargins(3, 3, 3, 3)
        
        
        
           # Create a QVBoxLayout for the centralWidget
        centralLayout = QtWidgets.QVBoxLayout(self.centralWidget())
        centralLayout.addLayout(topLayout)
        
        centralLayout.setContentsMargins(3, 3, 3, 3)
               
        self.show()
        
        
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
    

    
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    window = MainwindowSerialMonitor()
    
    app.exec()