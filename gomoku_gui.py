from random import randint
import sys
from time import sleep
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtGui
from gomoku_lib import Gomoku
from PyQt5.QtCore import *
import numpy as np
from generator import Generator

form_class = uic.loadUiType("gomoku.ui")[0]


gomoku_map = np.array([[-1 for _ in range(15)] for _ in range(15)])
my_color = 0
player_color = 1


class MySignal(QObject):

    connected = pyqtSignal(bool)
    ready = pyqtSignal(bool)
    updateAfterReady = pyqtSignal(tuple)
    updateOther = pyqtSignal(tuple)
    updateMine = pyqtSignal(tuple)
    end = pyqtSignal(tuple)
    

class Communicator(QThread):

    mysignal = MySignal()
    gomoku = None
    string = "before"


    def __init__(self, command):
        super().__init__()
        self.running = True
        self.command = command
        self.generator = None


    def run(self):
        if self.command == "CONNECT":
            ret = self.gomoku.connect()
            self.mysignal.connected.emit(ret)

        elif self.command == "READY":
            ret = self.gomoku.ready()
            self.mysignal.ready.emit(ret)
            
            success, cmd, turn, data = self.gomoku.update_or_end()

            self.mysignal.updateAfterReady.emit((turn, data))
            global my_color

            if turn == 1:
                my_color = 1
                success, cmd, turn, data = self.gomoku.update_or_end()
                if cmd == 2:
                    data = int(data)
                    x = int(data >> 4)
                    y = int(data & 0b00001111)
                    gomoku_map[x-1][y-1] = int(not my_color)
                    self.mysignal.updateOther.emit((x, y))

            self.generator = Generator(my_color, gomoku_map)
            
            while True:
                x, y = self.generator.gen_xy(my_color)
                self.gomoku.put(x+1, y+1)
                success, cmd, turn, data = self.gomoku.update_or_end()
                if cmd == 2:
                    gomoku_map[x][y] = my_color
                    self.generator.map[x][y] = my_color
                    self.mysignal.updateMine.emit((x+1, y+1))

                else:
                    self.mysignal.end.emit((turn, int(data)))
                    break
                
                success, cmd, turn, data = self.gomoku.update_or_end()
                
                if cmd == 2:
                    data = int(data)
                    x = int(data >> 4)
                    y = int(data & 0b00001111)
                    gomoku_map[x-1][y-1] = int(not my_color)
                    self.generator.map[x-1][y-1] = int(not my_color)
                    self.mysignal.updateOther.emit((x, y))

                else:
                    self.mysignal.end.emit((turn, int(data)))
                    break


    def resume(self):
        self.running = True


    def pause(self):
        self.running = False


class WindowClass(QMainWindow, form_class) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)

        self.pushButton_connect.clicked.connect(self.btnConnectFunction)
        Communicator.mysignal.connected.connect(self.afterConnectFunction)

        self.pushButton_ready.clicked.connect(self.btnReadyFunction)
        Communicator.mysignal.ready.connect(self.afterReadyFunction)
        Communicator.mysignal.updateAfterReady.connect(self.updateAfterReadyFunction)
        Communicator.mysignal.updateOther.connect(self.updateOtherFunction)
        Communicator.mysignal.updateMine.connect(self.updateMineFunction)
        Communicator.mysignal.end.connect(self.endFunction)

        self.radioButton_black.clicked.connect(self.btnRadioFunction)
        self.radioButton_white.clicked.connect(self.btnRadioFunction)
        self.radioButton_white.setChecked(True)

        self.addr = ""
        self.port = 0

        self.gomoku = None
        self.ready = False
        self.color = 0
        self.stoneLabels = []
        self.color_dict = {0: "black", 1: "white"}


    @pyqtSlot()
    def on_finished(self):
        print("finish thread")


    def btnConnectFunction(self):
        try:
            self.addr = self.lineEdit_addr.text()
            self.port = int(self.lineEdit_port.text())


            self.textBrowser_log.append("Connecting {}:{}...".format(self.addr, self.port))
            
            Communicator.gomoku = Gomoku(self.addr, self.port, True)
            self.pushButton_connect.setEnabled(False)
            self.lineEdit_addr.setEnabled(False)
            self.lineEdit_port.setEnabled(False)
            connect_communicator = Communicator("CONNECT")
            connect_communicator.finished.connect(self.on_finished)
            connect_communicator.start()
            sleep(0.1)

        except Exception as e:
            self.textBrowser_log.append("Error: " + str(e))
    

    @pyqtSlot(bool)
    def afterConnectFunction(self, connection):
        if not connection:
            self.pushButton_connect.setEnabled(True)
            self.lineEdit_addr.setEnabled(True)
            self.lineEdit_port.setEnabled(True)

        self.textBrowser_log.append("Connection status: " + str(connection))


    def btnReadyFunction(self):
        self.pushButton_ready.setEnabled(False)
        ready_communicator = Communicator("READY")
        ready_communicator.finished.connect(self.on_finished)
        ready_communicator.start()
        sleep(0.1)


    @pyqtSlot(bool)
    def afterReadyFunction(self, status):
        if not status:
            self.pushButton_ready.setEnabled(True)
        
        self.textBrowser_log.append("Ready status: " + str(status))
        self.ready = True

        
    @pyqtSlot(tuple)
    def updateAfterReadyFunction(self, ret):
        turn, data = ret
        global my_color
        if turn == 0:
            self.color = 0
            my_color = 0
            self.textBrowser_log.append("You are " + self.color_dict[self.color])
            self.textBrowser_log.append("Your turn")
        else:
            self.color = 1
            my_color = 1
            self.textBrowser_log.append("You are " + self.color_dict[self.color])
            self.textBrowser_log.append("Other's turn")
        
    
    @pyqtSlot(tuple)
    def updateOtherFunction(self, pos):
        x, y = pos
        self.addStone(x, y, self.color_dict[int(not self.color)])
        self.textBrowser_log.append("Other put at " + str(x) + ", " + str(y))
    

    @pyqtSlot(tuple)
    def updateMineFunction(self, pos):
        x, y = pos
        self.addStone(x, y, self.color_dict[self.color])
        self.textBrowser_log.append("You put at" + str(x) + ", " + str(y))


    @pyqtSlot(tuple)
    def endFunction(self, data):
        turn, data = data

        if data == 0 :
            result = "error"
        elif data == 1:
            result = "time out"
        else:
            x = data >> 4
            y = data & 0b00001111
            result = "connect5 when put at {}, {}".format(x, y)
            color = int( not (self.color ^ turn))
            self.addStone(x, y, self.color_dict[color])

        if turn == 1:
            self.textBrowser_log.append("Win! ({})".format(result))
        elif turn == 0:
            self.textBrowser_log.append("Lose! ({})".format(result))


    def btnRadioFunction(self):
        global my_color, player_color

        if self.radioButton_black.isChecked() : 
            my_color = 1
            player_color = 0

        elif self.radioButton_white.isChecked() : 
            my_color = 0
            player_color = 1


    def btnPlayFunction(self):
        pass


    def btnPutFunction(self):
        pass


    def addStone(self, x, y, color):
        label = QLabel(self)
        label.setPixmap(QtGui.QPixmap(":/icon/" + color + ".png"))
        label.setGeometry(int((587 * x - 349) / 14), int((293 * y - 104) / 7), 40, 40)
        label.setVisible(True)
        
    


if __name__ == "__main__" :
    app = QApplication(sys.argv) 
    myWindow = WindowClass() 
    myWindow.show()
    app.exec_()