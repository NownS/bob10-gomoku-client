import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic, QtGui
from gomoku_lib import Gomoku

form_class = uic.loadUiType("gomoku.ui")[0]

class WindowClass(QMainWindow, form_class) :
    def __init__(self) :
        super().__init__()
        self.setupUi(self)

        self.pushButton_connect.clicked.connect(self.btnConnectFunction)
        self.pushButton_ready.clicked.connect(self.btnReadyFunction)
        self.pushButton_play.clicked.connect(self.btnPlayFunction)
        self.pushButton_put.clicked.connect(self.btnPutFunction)

        self.addr = ""
        self.port = 0
        self.gomoku = None
        self.ready = False
        self.color = 0
        self.stoneLabels = []
        self.color_dict = {0: "black", 1: "white"}

    def btnConnectFunction(self):
        try:
            self.addr = self.lineEdit_addr.text()
            self.port = int(self.lineEdit_port.text())
            self.textBrowser_log.append("Connecting {}:{}...".format(self.addr, self.port))
            self.gomoku = Gomoku(self.addr, self.port, True)
            self.textBrowser_log.append("Connection status: " + str(self.gomoku.connect()))
        except Exception as e:
            self.textBrowser_log.append("Error: " + str(e))
    

    def btnReadyFunction(self):
        stat = self.gomoku.ready()
        self.textBrowser_log.append("Ready status: " + str(stat))
        self.ready = True
        while True:
            success, cmd, turn, data = self.gomoku.update_or_end()
            if success:
                break
        if turn == 0:
            self.color = 0
            self.textBrowser_log.append("You are " + self.color_dict[self.color])
            self.textBrowser_log.append("Your turn")
            return
        else:
            self.color = 1
            self.textBrowser_log.append("You are " + self.color_dict[self.color])
            self.textBrowser_log.append("Other's turn")
            while True:
                success, cmd, turn, data = self.gomoku.update_or_end()
                if success:
                    break
            data = int(data)
            x = int(data >> 4)
            y = int(data & 0b00001111)
            self.textBrowser_log.append("Other put at " + str(x) + ", " + str(y))
            self.addStone(x, y, "black")
        

    def btnPlayFunction(self):
        self.textBrowser_log.append("Play")
    
    
    def btnPutFunction(self):
        x = int(self.lineEdit_x.text())
        y = int(self.lineEdit_y.text())
        self.textBrowser_log.append("Put " + str(x) + ", " + str(y))
        ret = False
        while not ret:
            ret = self.gomoku.put(x, y)
        self.lineEdit_x.setText("")
        self.lineEdit_y.setText("")
        while True:
            success, cmd, turn, data = self.gomoku.update_or_end()
            if success:
                break
        
        if cmd == 2:
            color = self.color
            x = data >> 4
            y = data & 0b00001111
            self.addStone(x, y, self.color_dict[color])

        elif cmd == 4:
            if data == 0 :
                result = "error"
            elif data == 1:
                result = "time out"
            else:
                result = "connect5"
                x = data >> 4
                y = data & 0b00001111
                color = int( not (self.color ^ turn))
                self.addStone(x, y, self.color_dict[color])

            if turn == 1:
                self.textBrowser_log.append("Win! ({})".format(result))
            elif turn == 0:
                self.textBrowser_log.append("Lose! ({})".format(result))
            return

        while True:
            success, cmd, turn, data = self.gomoku.update_or_end()
            if success:
                break

        if cmd == 2:
            color = int(not self.color)
            x = data >> 4
            y = data & 0b00001111
            self.addStone(x, y, self.color_dict[color])
            self.textBrowser_log.append("Other put at " + str(x) + ", " + str(y))

        elif cmd == 4:
            if data == 0 :
                result = "error"
            elif data == 1:
                result = "time out"
            else:
                result = "connect5"
                x = data >> 4
                y = data & 0b00001111
                color = int( not (self.color ^ turn))
                self.addStone(x, y, self.color_dict[color])

            if turn == 1:
                self.textBrowser_log.append("Win! ({})".format(result))
            elif turn == 0:
                self.textBrowser_log.append("Lose! ({})".format(result))
            return


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