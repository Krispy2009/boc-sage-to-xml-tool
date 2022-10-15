import sys
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QFileDialog,
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

        self.window = QWidget()
        self.window.setWindowTitle("SAGE 50 <=> Bank of Cyprus XML tool ")
        self.window.setGeometry(100, 100, 500, 180)

        fileInputLayout = QVBoxLayout()

        self.initUploadLabel()
        self.initUploadButton()
        fileInputLayout.addWidget(self.uploadLabel)
        fileInputLayout.addWidget(self.uploadButton)

        self.window.setLayout(fileInputLayout)
        self.window.show()

    def initUploadLabel(self):
        self.uploadLabel = QLabel(self.DEFAULT_LABEL_TEXT)
        self.uploadLabel.setStyleSheet("border: 1px solid #222")
        self.uploadLabel.setMaximumHeight(30)
        self.uploadLabel.mousePressEvent = self.onClickLabel

    def initUploadButton(self):
        self.uploadButton = QPushButton("Upload")
        self.uploadButton.mousePressEvent = self.onClickUploadButton

    def onClickLabel(self, event):
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.AnyFile)
        filename = dialog.getOpenFileName(self.window)
        if filename[0] != "":
            self.uploadLabel.setText(filename[0])

    def onClickUploadButton(self, event):
        if self.uploadLabel.text() != self.DEFAULT_LABEL_TEXT:
            self.uploadButton.animateClick()
            print(f"will upload {self.uploadLabel.text()}")
            self.filenameToUpload = self.uploadLabel.text()
            self.generate_xml_from_file(self.filenameToUpload)

    def generate_xml_from_file(self, filename):
        print("Uploadinggggg")
        transactions = parse_sage_report(filename)
        transactions = do_calcs(transactions)
        boc_xml = BoCXML(transactions)
        boc_xml.build_xml(transactions)


SageToBOCXMLTool()

sys.exit(app.exec())
