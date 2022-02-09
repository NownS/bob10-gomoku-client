from PyQt5.QtWidgets import *
import sys
from gomoku_gui import WindowClass

if __name__ == "__main__" :
    app = QApplication(sys.argv) 
    myWindow = WindowClass() 
    myWindow.show()
    app.exec_()