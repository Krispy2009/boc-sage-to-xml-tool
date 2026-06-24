# boc-sage-to-xml-tool
A tool to convert a Sage report to Bank Of Cyprus xml format for multiple payments

This tool is still in its early stages, but I have used it for my own use successfully.
It is tailored to what I need at the moment but feel free to open an issue or PR to discuss any changes you need.

## Install
1. Install requirements `pip install -r requirements.txt`
2. Optional if you are using the GUI: `pip install -r gui/requirements_gui.txt`

## Running in the terminal
1. Make sure you have a sage report in the current directory (see sample.xlsx)
2. Make sure you have the following env variables exported (I use [direnv](https://direnv.net/) to manage my env variables in a .env file):
```
COMPANY_NAME=<your company name>
COMPANY_IBAN=<your company IBAN>
```
3. Make sure the filename in `main.py` corresponds to your report's filename.
4. Run `python main.py`
   - By default the payments use today's date as the execution date.
   - To set a future execution date, pass it as `YYYY-MM-DD`, e.g. `python main.py 2026-07-01`.
5. The XML should be created in the current directory 🎉


## Running the GUI
1. Run `python gui/boc-gui.py`
2. The first time, click **Settings** and enter your **Company name** and **Company IBAN**
   (the debtor details). These are saved on your machine and remembered between runs,
   so you only need to do this once — the GUI does not use the `COMPANY_NAME` /
   `COMPANY_IBAN` environment variables.
3. Click the label to select your Sage report (`.xlsx`).
4. Pick the **Payment execution date** (defaults to today; past dates are not allowed).
5. Click **Upload**. The XML is generated next to the report you selected.


## Packaging the GUI into an executable
We use [PyInstaller](https://pyinstaller.org/) to bundle the GUI into a standalone
executable so end users don't need Python installed.

> **Note:** PyInstaller cannot cross-compile. You must build the Windows `.exe` on a
> Windows machine and the macOS app on a Mac.

First, install the dependencies (ideally in a virtual environment):
```
pip install -r requirements.txt
pip install -r gui/requirements_gui.txt
```

### Windows
Use the Windows spec file. From the repo root run:
```
pyinstaller boc-gui-windows.spec
```
The executable is created at `dist/sage-to-BOC-XML.exe`.

### macOS
Use the macOS spec file. From the repo root run:
```
pyinstaller boc-gui-mac.spec
```
The app is created at `dist/sage-to-BOC-XML.app` (with the raw binary at `dist/sage-to-BOC-XML`).

The build artifacts land in `dist/`, with intermediate files in `build/`.

Reference: [Packaging PyQt6 applications with PyInstaller](https://www.pythonguis.com/tutorials/packaging-pyqt6-applications-windows-pyinstaller/)
