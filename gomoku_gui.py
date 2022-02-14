from itertools import starmap
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

    time_start = pyqtSignal()
    time_stop = pyqtSignal()

    someone_end = pyqtSignal(tuple)

    add_stone = pyqtSignal(int, int, str)
    finish = pyqtSignal()


class Communicator(QThread):

    mysignal = MySignal()
    gomoku = None

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
                self.mysignal.time_start.emit()
                my_color = 1
                success, cmd, turn, data = self.gomoku.update_or_end()
                if cmd == 2:
                    data = int(data)
                    x = int(data >> 4)
                    y = int(data & 0b00001111)
                    gomoku_map[x-1][y-1] = int(not my_color)
                    self.mysignal.updateOther.emit((x, y))
                    self.mysignal.time_stop.emit()
            

            self.generator = Generator(my_color, gomoku_map)
            
            while True:
                self.mysignal.time_start.emit()
                x, y = self.generator.gen_xy(my_color)
                self.gomoku.put(x+1, y+1)
                success, cmd, turn, data = self.gomoku.update_or_end()
                if cmd == 2:
                    gomoku_map[x][y] = my_color
                    self.generator.map[x][y] = my_color
                    self.mysignal.updateMine.emit((x+1, y+1))
                    self.mysignal.time_stop.emit()

                else:
                    self.mysignal.end.emit((turn, int(data)))
                    self.mysignal.time_stop.emit()
                    break
                
                self.mysignal.time_start.emit()
                success, cmd, turn, data = self.gomoku.update_or_end()
                
                if cmd == 2:
                    data = int(data)
                    x = int(data >> 4)
                    y = int(data & 0b00001111)
                    gomoku_map[x-1][y-1] = int(not my_color)
                    self.generator.map[x-1][y-1] = int(not my_color)
                    self.mysignal.updateOther.emit((x, y))
                    self.mysignal.time_stop.emit()

                else:
                    self.mysignal.end.emit((turn, int(data)))
                    self.mysignal.time_stop.emit()
                    break


    def resume(self):
        self.running = True


    def pause(self):
        self.running = False


class WindowClass(QMainWindow, form_class) :
    
    mysignal = MySignal()
    
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

        self.label_green.setHidden(True)
        self.label_color.setHidden(False)
        self.label_black.setHidden(True)
        self.label_white.setHidden(True)

        self.label_color_your.setHidden(False)
        self.label_black_your.setHidden(True)
        self.label_white_your.setHidden(True)

        self.timer = QTimer(self)
        self.timer.setInterval(50)
        self.timer.timeout.connect(self.timeout)
        self.time = None
        Communicator.mysignal.time_stop.connect(self.timer_stop)
        Communicator.mysignal.time_start.connect(self.timer_start)



        self.pushButton_play.clicked.connect(self.btnPlayFunction)
        self.pushButton_put.clicked.connect(self.btnPutFunction)
        self.computer = None
        ComputerPlayer.mysignal.add_stone.connect(self.addStone)
        ComputerPlayer.mysignal.finish.connect(self.btnPutActiveFunction)
        ComputerPlayer.mysignal.someone_end.connect(self.someoneEnd)
        self.mysignal.someone_end.connect(self.someoneEnd)
        self.turn = 0
        self.isMulti = True
        self.mysignal.time_stop.connect(self.timer_stop)
        self.mysignal.time_start.connect(self.timer_start)


    @pyqtSlot()
    def timer_start(self):
        self.time = QTime.currentTime()
        self.timer.start()

    
    @pyqtSlot()
    def timer_stop(self):
        self.timer.stop()

    
    def timeout(self):
        sender = self.sender()
        interval = QTime.currentTime().secsTo(self.time) + 15

        if id(sender) == id(self.timer):
            self.label_time.setText(str(interval))
            if interval <= 0 and not self.isMulti:
                self.mysignal.someone_end.emit((3, self.turn))


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
            self.radioButton_black.setEnabled(False)
            self.radioButton_white.setEnabled(False)
            self.pushButton_play.setEnabled(False)
            self.pushButton_put.setEnabled(False)
            self.lineEdit_x.setEnabled(False)
            self.lineEdit_y.setEnabled(False)
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
            self.radioButton_black.setEnabled(True)
            self.radioButton_white.setEnabled(True)
            self.pushButton_play.setEnabled(True)
            self.pushButton_put.setEnabled(True)
            self.lineEdit_x.setEnabled(True)
            self.lineEdit_y.setEnabled(True)

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
        self.label_black.setHidden(False)

        
    @pyqtSlot(tuple)
    def updateAfterReadyFunction(self, ret):
        self.timer_start()

        turn, data = ret
        global my_color
        if turn == 0:
            self.color = 0
            my_color = 0
            self.textBrowser_log.append("You are " + self.color_dict[self.color])
            self.textBrowser_log.append("Your turn")
            self.label_black_your.setHidden(False)
        else:
            self.color = 1
            my_color = 1
            self.textBrowser_log.append("You are " + self.color_dict[self.color])
            self.textBrowser_log.append("Other's turn")
            self.label_white_your.setHidden(False)
        
             
    
    @pyqtSlot(tuple)
    def updateOtherFunction(self, pos):
        self.timer_start()

        x, y = pos
        self.addStone(x, y, self.color_dict[int(not self.color)])
        self.textBrowser_log.append("Other put at " + str(x) + ", " + str(y))
    

    @pyqtSlot(tuple)
    def updateMineFunction(self, pos):
        self.timer_start()

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
        self.isMulti = False
        self.radioButton_black.setEnabled(False)
        self.radioButton_white.setEnabled(False)
        self.pushButton_play.setEnabled(False)
        self.pushButton_connect.setEnabled(False)
        self.pushButton_ready.setEnabled(False)
        self.lineEdit_addr.setEnabled(False)
        self.lineEdit_port.setEnabled(False)
        self.textBrowser_log.append("Solo Play Start")
        self.computer = ComputerPlayer()
        
        self.mysignal.time_start.emit()

        self.label_black.setHidden(False)
        
        if not my_color:
            self.label_white_your.setHidden(False)
            self.computer.start()
            self.turn = 1
            sleep(0.1)
        else:
            self.label_black_your.setHidden(False)


    def btnPutFunction(self):
        self.mysignal.time_stop.emit()
        self.pushButton_put.setEnabled(False)
        self.lineEdit_x.setEnabled(False)
        self.lineEdit_y.setEnabled(False)
        self.computer.args[0] = int(self.lineEdit_x.text())
        self.computer.args[1] = int(self.lineEdit_y.text())
        self.mysignal.time_start.emit()
        self.computer.start()
        self.turn = 1
        sleep(0.1)


    @pyqtSlot()
    def btnPutActiveFunction(self):
        self.mysignal.time_stop.emit()
        self.pushButton_put.setEnabled(True)
        self.lineEdit_x.setEnabled(True)
        self.lineEdit_y.setEnabled(True)
        self.turn = 0
        self.mysignal.time_start.emit()


    @pyqtSlot(tuple)
    def someoneEnd(self, data):
        ret, stone = data
        if ret == 1:
            if stone == my_color:
                self.textBrowser_log.append("You Win By Error")
                self.mysignal.time_stop.emit()
            else:
                self.textBrowser_log.append("You Lose By Error")
                self.mysignal.time_stop.emit()
        elif ret == 2:
            if stone == my_color:
                self.textBrowser_log.append("You Lose By Connect5")
                self.mysignal.time_stop.emit()
            else:
                self.textBrowser_log.append("You Win By Connect5")
                self.mysignal.time_stop.emit()
        else:
            
            self.pushButton_put.setEnabled(False)
            self.lineEdit_x.setEnabled(False)
            self.lineEdit_y.setEnabled(False)
            
            if stone:
                self.textBrowser_log.append("You Win By Time-Over")
                self.computer.terminate()
                self.mysignal.time_stop.emit()
                
            else:
                self.textBrowser_log.append("You Lose By Time-Over")
                self.mysignal.time_stop.emit()



    @pyqtSlot(int, int, str)
    def addStone(self, x, y, color):
        label = QLabel(self)
        label.setPixmap(QtGui.QPixmap(":/icon/" + color + ".png"))
        label.setGeometry(int((587 * x - 349) / 14), int((293 * y - 104) / 7), 40, 40)
        label.setVisible(True)
        self.label_green.setHidden(False)
        self.label_color.setHidden(False)
        self.label_green.setGeometry(int((587 * x - 349) / 14) + 10, int((293 * y - 104) / 7) + 10, 20, 20)
        self.label_green.raise_()
        self.label_black.setHidden(color == "black")
        self.label_white.setHidden(color == "white")
        

def column(matrix, i):
    ret = []
    for row in matrix:
        ret.append(row[i])
    return ret


def diagonal(matrix, x, y):
    diag1 = []
    diag2 = []

    x_iter, y_iter = x, y
    while (x_iter > 0 and y_iter > 0):
        x_iter -= 1
        y_iter -= 1
    while (x_iter < 15 and y_iter < 15):
        diag1.append(matrix[x_iter][y_iter])
        x_iter += 1
        y_iter += 1
    
    x_iter, y_iter = x, y
    while (x_iter > 0 and y_iter < 14):
        x_iter -= 1
        y_iter += 1
    while (x_iter < 15 and y_iter > -1):
        diag2.append(matrix[x_iter][y_iter])
        x_iter += 1
        y_iter -= 1
    
    return diag1, diag2


def find_cannot_place(x_idx, y_idx, color_id):
    if color_id == 0:
        
        ROW, COL, DIAG_1, DIAG_2 = 0, 1, 2, 3

        last_point = [[] for _ in range(4)]

        len_stone = [-1 for _ in range(4)]

        i, j = x_idx, y_idx
        while -1 < i < 15 and gomoku_map[i][j] == color_id:
            len_stone[ROW] += 1
            i -= 1
        last_point[ROW].append((i, j))

        i, j = x_idx, y_idx
        while -1 < i < 15 and gomoku_map[i][j] == color_id:
            len_stone[ROW] += 1
            i += 1
        last_point[ROW].append((i, j))
        
        i, j = x_idx, y_idx
        while -1 < j < 15 and gomoku_map[i][j] == color_id:
            len_stone[COL] += 1
            j -= 1
        last_point[COL].append((i, j))

        i, j = x_idx, y_idx
        while -1 < j < 15 and gomoku_map[i][j] == color_id:
            len_stone[COL] += 1
            j += 1
        last_point[COL].append((i, j))
        
        i, j = x_idx, y_idx
        while -1 < j < 15 and -1 < i < 15 and gomoku_map[i][j] == color_id:
            len_stone[DIAG_1] += 1
            j -= 1
            i -= 1
        last_point[DIAG_1].append((i,j))
        
        i, j = x_idx, y_idx
        while -1 < j < 15 and -1 < i < 15 and gomoku_map[i][j] == color_id:
            len_stone[DIAG_1] += 1
            j += 1
            i += 1
        last_point[DIAG_1].append((i,j))
        
        i, j = x_idx, y_idx
        while -1 < j < 15 and -1 < i < 15 and gomoku_map[i][j] == color_id:
            len_stone[DIAG_2] += 1
            j += 1
            i -= 1
        last_point[DIAG_2].append((i,j))
        
        i, j = x_idx, y_idx
        while -1 < j < 15 and -1 < i < 15 and gomoku_map[i][j] == color_id:
            len_stone[DIAG_2] += 1
            j -= 1
            i += 1
        last_point[DIAG_2].append((i,j))

        check_3_idx = []
        check_4_idx = []

        for idx in range(4):
            if len_stone[idx] == 3:
                check_3_idx.append(idx)
            elif len_stone[idx] == 4:
                check_4_idx.append(idx)
        
        if len(check_3_idx) >= 2:
            count_3 = 0
            for idx in check_3_idx:
                blocked = False
                for x, y in last_point[idx]:
                    if 0 <= x <= 14 and 0 <= y <= 14 and gomoku_map[x][y] == -1:
                        continue
                    else:
                        blocked = True
                        break
                if not blocked:
                    count_3 += 1

            if count_3 >= 2:
                return True

        if len(check_4_idx) >= 2:
            count_4 = 0
            for idx in check_4_idx:
                blocked = False
                for x, y in last_point[idx]:
                    if 0 <= x <= 14 and 0 <= y <= 14 and gomoku_map[x][y] == -1:
                        continue
                    else:
                        blocked = True
                        break
                if not blocked:
                    count_4 += 1
            
            if count_4 >= 2:
                return True

    return False


def someone_win(x_idx, y_idx, color_id):
    row = gomoku_map[x_idx]
    col = column(gomoku_map, y_idx)
    diag = diagonal(gomoku_map, x_idx, y_idx)

    for candidate in [row, col, *diag]:
        length = 0
        length_list = []
        for i in range(len(candidate)):
            if candidate[i] == color_id:
                length += 1
            else:
                length_list.append(length)
                length = 0
        
        if color_id == 0:
            try:
                id = length_list.index(5)
                return True
            except ValueError:
                continue
        else:
            if length_list and max(length_list) >= 5:
                return True

    return False


class ComputerPlayer(QThread):

    mysignal = MySignal()

    def __init__(self):
        super().__init__()
        self.generator = Generator(my_color, gomoku_map)
        self.color_str = ["black", "white"]
        self.args = [0, 0, 0]

    
    def run(self):
        player_x, player_y, turn = self.args
        if turn or not player_color:
            ret = self.check(player_color, player_x, player_y)
            self.args[2] += 1
            if not ret:
                self.generator.map[player_x-1][player_y-1] = player_color
                self.mysignal.add_stone.emit(player_x, player_y, self.color_str[player_color])
            else:
                if ret == 2:
                    self.mysignal.add_stone.emit(player_x, player_y, self.color_str[player_color])
                self.mysignal.someone_end.emit((ret, player_color))
                return
        
        
        x, y = self.generator.gen_xy(my_color)
        
        ret = self.check(my_color, x+1, y+1)
        self.args[2] += 1
        if not ret:
            self.generator.map[x][y] = my_color
            self.mysignal.add_stone.emit(x+1, y+1, self.color_str[my_color])
        else:
            if ret == 2:
                self.mysignal.add_stone.emit(x+1, y+1, self.color_str[my_color])
            self.mysignal.someone_end.emit((ret, my_color))
            return
        self.mysignal.finish.emit()
        

    def check(self, color_id, x, y):
        x_idx = x-1
        y_idx = y-1

        if not(0 < x < 16 and 0 < y < 16) :
            return 1

        if gomoku_map[x_idx][y_idx] != -1:
            return 1

        gomoku_map[x_idx][y_idx] = color_id

        if find_cannot_place(x_idx, y_idx, color_id):
            return 1

        if someone_win(x_idx, y_idx, color_id):
            return 2
        
        return 0


if __name__ == "__main__" :
    app = QApplication(sys.argv) 
    myWindow = WindowClass() 
    myWindow.show()
    app.exec_()