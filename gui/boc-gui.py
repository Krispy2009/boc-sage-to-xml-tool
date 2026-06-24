import os
import sys

# Allow running directly (`python gui/boc-gui.py`) by putting the repo root,
# where helpers.py and boc_xml.py live, on the import path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PyQt6.QtCore import QDate, QSettings
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QPushButton,
    QFileDialog,
    QDateEdit,
    QDialog,
    QFormLayout,
    QLineEdit,
    QDialogButtonBox,
)

from helpers import parse_sage_report, do_calcs
from boc_xml import BoCXML

app = QApplication([])
# Identify where QSettings persists (Mac plist / Windows registry).
app.setOrganizationName("BankOfCyprus")
app.setApplicationName("SageToBOCXMLTool")


class SettingsDialog(QDialog):
    """Lets the user store their company name and IBAN (the debtor details)."""

    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Company settings")

        self.nameEdit = QLineEdit(settings.value("company_name", "", str))
        self.ibanEdit = QLineEdit(settings.value("company_iban", "", str))

        form = QFormLayout()
        form.addRow("Company name", self.nameEdit)
        form.addRow("Company IBAN", self.ibanEdit)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.onSave)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout()
        layout.addLayout(form)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def onSave(self):
        self.settings.setValue("company_name", self.nameEdit.text().strip())
        self.settings.setValue("company_iban", self.ibanEdit.text().replace(" ", ""))
        self.accept()


class SageToBOCXMLTool:
    DEFAULT_LABEL_TEXT = "Click here to select a file"

    def __init__(self):
        self.filenameToUpload = None
        self.uploadLabel = None
        self.uploadButton = None
        self.quitButton = None
        self.settingsButton = None
        self.statusLabel = None
        self.dateLabel = None
        self.dateEdit = None

        self.settings = QSettings()

        self.window = QWidget()
        self.window.setWindowTitle("SAGE 50 <=> Bank of Cyprus XML tool ")
        self.window.setGeometry(100, 100, 500, 260)

        fileInputLayout = QVBoxLayout()

        self.initUploadLabel()
        self.initDateSelector()
        self.initUploadButton()
        self.initSettingsButton()
        self.initStatusLabel()
        self.initQuitButton()
        fileInputLayout.addWidget(self.uploadLabel)
        fileInputLayout.addWidget(self.dateLabel)
        fileInputLayout.addWidget(self.dateEdit)
        fileInputLayout.addWidget(self.statusLabel)
        fileInputLayout.addWidget(self.uploadButton)
        fileInputLayout.addWidget(self.settingsButton)
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

    def initSettingsButton(self):
        self.settingsButton = QPushButton("Settings")
        self.settingsButton.mousePressEvent = self.onClickSettings

    def initQuitButton(self):
        self.quitButton = QPushButton("Quit")
        self.quitButton.mousePressEvent = self.onQuit

    def onClickSettings(self, event):
        dialog = SettingsDialog(self.settings, self.window)
        dialog.exec()

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
        company_name = self.settings.value("company_name", "", str)
        company_iban = self.settings.value("company_iban", "", str)
        if not company_name or not company_iban:
            self.statusLabel.setText("Set your company name and IBAN in Settings first")
            self.statusLabel.setStyleSheet("color:red")
            return

        self.statusLabel.setStyleSheet("color:black")
        self.statusLabel.setText(f"Generating XML file")
        try:
            transactions = parse_sage_report(filename)
            transactions = do_calcs(transactions)
            execution_date = self.dateEdit.date().toPyDate()
            # Write the XML next to the report the user selected, since the app's
            # working directory may be read-only when launched from Finder.
            output_dir = os.path.dirname(filename)
            boc_xml = BoCXML(
                transactions,
                execution_date=execution_date,
                company_name=company_name,
                company_iban=company_iban,
                output_dir=output_dir,
            )
        except Exception as error:
            self.statusLabel.setText(f"Error: {error}")
            self.statusLabel.setStyleSheet("color:red")
            return
        self.statusLabel.setText(f"File created: {boc_xml.document}")

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
