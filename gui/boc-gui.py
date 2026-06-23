import os
import sys

# Allow running directly (`python gui/boc-gui.py`) by putting the repo root,
# where helpers.py and boc_xml.py live, on the import path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import QDate
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QFileDialog,
    QDateEdit,
)

from helpers import parse_sage_report, do_calcs
from boc_xml import BoCXML

app = QApplication([])


class SageToBOCXMLTool:
    DEFAULT_LABEL_TEXT = "Click here to select a file"

    def __init__(self):
        self.filenameToUpload = None
        self.uploadLabel = None
        self.uploadButton = None
        self.quitButton = None
        self.statusLabel = None
        self.dateLabel = None
        self.dateEdit = None

        self.window = QWidget()
        self.window.setWindowTitle("SAGE 50 <=> Bank of Cyprus XML tool ")
        self.window.setGeometry(100, 100, 500, 220)

        fileInputLayout = QVBoxLayout()

        self.initUploadLabel()
        self.initDateSelector()
        self.initUploadButton()
        self.initStatusLabel()
        self.initQuitButton()
        fileInputLayout.addWidget(self.uploadLabel)
        fileInputLayout.addWidget(self.dateLabel)
        fileInputLayout.addWidget(self.dateEdit)
        fileInputLayout.addWidget(self.statusLabel)
        fileInputLayout.addWidget(self.uploadButton)
        fileInputLayout.addWidget(self.quitButton)

        self.window.setLayout(fileInputLayout)
        self.window.show()

    def initDateSelector(self):
        self.dateLabel = QLabel("Payment execution date")
        self.dateLabel.setMaximumHeight(30)

        self.dateEdit = QDateEdit()
        self.dateEdit.setCalendarPopup(True)
        self.dateEdit.setDisplayFormat("yyyy-MM-dd")
        # Default to today and don't allow execution dates in the past
        self.dateEdit.setDate(QDate.currentDate())
        self.dateEdit.setMinimumDate(QDate.currentDate())

    def initStatusLabel(self):
        self.statusLabel = QLabel()
        self.statusLabel.setMaximumHeight(30)

    def initUploadLabel(self):
        self.uploadLabel = QLabel(self.DEFAULT_LABEL_TEXT)
        self.uploadLabel.setStyleSheet("border: 1px solid #222")
        self.uploadLabel.setMaximumHeight(30)
        self.uploadLabel.mousePressEvent = self.onClickLabel

    def initUploadButton(self):
        self.uploadButton = QPushButton("Upload")
        self.uploadButton.mousePressEvent = self.onClickUploadButton

    def initQuitButton(self):
        self.quitButton = QPushButton("Quit")
        self.quitButton.mousePressEvent = self.onQuit

    def onClickLabel(self, event):
        dialog = QFileDialog()

        filename = dialog.getOpenFileName(self.window)
        if self.isValidFileType(filename[0]):
            self.uploadLabel.setText(filename[0])
            self.filenameToUpload = filename[0]

    def onClickUploadButton(self, event):
        if self.filenameToUpload is not None:
            self.uploadButton.animateClick()
            print(f"will upload {self.filenameToUpload}")
            self.generate_xml_from_file(self.filenameToUpload)
            self.filenameToUpload = None
            self.uploadLabel.setText(self.DEFAULT_LABEL_TEXT)

    def generate_xml_from_file(self, filename):
        self.statusLabel.setText(f"Generating XML file")
        transactions = parse_sage_report(filename)
        transactions = do_calcs(transactions)
        execution_date = self.dateEdit.date().toPyDate()
        boc_xml = BoCXML(transactions, execution_date=execution_date)
        filename = boc_xml.build_xml(transactions)
        self.statusLabel.setText(f"File created: {filename}")

    def isValidFileType(self, filename):
        if not filename.endswith("xlsx"):
            self.statusLabel.setText("Please select a .xlsx file")
            self.statusLabel.setStyleSheet("color:red")
            return False
        else:
            self.statusLabel.setText("")
            self.statusLabel.setStyleSheet("color:black")
            return True

    def onQuit(self, event):
        sys.exit()


SageToBOCXMLTool()

sys.exit(app.exec())
