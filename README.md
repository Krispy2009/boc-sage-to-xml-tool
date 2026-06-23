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
2. Click the label to select your Sage report (`.xlsx`).
3. Pick the **Payment execution date** (defaults to today; past dates are not allowed).
4. Click **Upload** to generate the XML in the current directory.


## Packaging GUI for distribution
This is still WIP - instructions [here](https://www.pythonguis.com/tutorials/packaging-pyqt6-applications-windows-pyinstaller/)
