#!/usr/bin/env python3
from PySide2 import QtWidgets
from widgets import WidgetMainWindow

import sys
import logging


def main():
    logging.basicConfig(filename="", level=logging.DEBUG, format="%(asctime)s - %(levelname)s: %(message)s")

    logging.info("Creating window...")
    app = QtWidgets.QApplication(sys.argv)

    main_window = WidgetMainWindow()
    main_window.show()
    main_window.resize(500, 600)

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
