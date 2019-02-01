from PySide2 import QtCore, QtWidgets, QtGui
import sys
from UI import Widget


def main():
    app = QtWidgets.QApplication([])
    # Instantiate UI with default window properties
    widget = Widget()
    widget.setFixedSize(300, 150)
    widget.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
