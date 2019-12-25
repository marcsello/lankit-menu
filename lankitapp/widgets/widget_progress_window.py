from ui import Ui_ProgressForm
from PySide2 import QtWidgets, QtCore


class WidgetProgressWindow(QtWidgets.QWidget):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.ui = Ui_ProgressForm()
        self.ui.setupUi(self)

        self.center()

        self.setFixedSize(self.size())
        self.setWindowFlags(QtCore.Qt.Dialog)

    def center(self):
        qRect = self.frameGeometry()
        centerPoint = QtWidgets.QDesktopWidget().availableGeometry().center()
        qRect.moveCenter(centerPoint)
        self.move(qRect.topLeft())

    def closeEvent(self, event):
        event.ignore()  # TODO: Abort?
