# Sage to Bank of Cyprus XML

Turn a Sage **Aged Creditors Analysis** report into a Bank of Cyprus bulk-payment file (ISO 20022 `pain.001.001.03` XML), ready to upload so you can pay many suppliers at once.

Runs from the terminal, or as a small desktop app (Windows and macOS).

> **Status:** early stage. It works for my own workflow and is tailored to one report layout (see `sample.xlsx`). There are no automated tests yet, so **always check the generated XML and the totals before uploading it to the bank.**
>
> Issues and PRs are welcome if you need a different layout.

## What it does

- Reads suppliers from a Sage creditors report (`.xlsx`), including the merged cells Sage exports
- Tidies the data: removes spaces from IBANs and unsupported characters from supplier names
- Writes one XML file with a payment per supplier, using today as the execution date or a future date you choose

## Install

1. Install the requirements: `pip install -r requirements.txt`
2. If you want the desktop app: `pip install -r gui/requirements_gui.txt`

## Run it in the terminal

1. Put your Sage report in the current directory (see `sample.xlsx` for the expected layout).
2. Export your company details (I use [direnv](https://direnv.net/) to keep these in a `.env` file):
   ```
   COMPANY_NAME=<your company name>
   COMPANY_IBAN=<your company IBAN>
   ```
3. Make sure the filename in `main.py` matches your report's filename.
4. Run `python main.py`.
   - By default the payments use today's date as the execution date.
   - For a future date, pass it as `YYYY-MM-DD`, e.g. `python main.py 2026-07-01`.
5. A timestamped XML file is created in the current directory. 🎉

## Run the desktop app

1. Run `python gui/boc-gui.py`.
2. The first time, click **Settings** and enter your **Company name** and **Company IBAN** (the debtor details). They are saved on your machine and remembered between runs. The app does not use the `COMPANY_NAME` / `COMPANY_IBAN` environment variables.
3. Click the label to choose your Sage report (`.xlsx`).
4. Pick the **payment execution date** (defaults to today; past dates aren't allowed).
5. Click **Upload**. The XML is created next to the report you selected.

## Package the app as an executable

[PyInstaller](https://pyinstaller.org/) bundles the app so end users don't need Python installed.

> PyInstaller can't cross-compile: build the Windows `.exe` on Windows and the macOS app on a Mac.

Install the dependencies first, ideally in a virtual environment:

```
pip install -r requirements.txt
pip install -r gui/requirements_gui.txt
```

**Windows:** `pyinstaller boc-gui-windows.spec` creates `dist/sage-to-BOC-XML.exe`.

**macOS:** `pyinstaller boc-gui-mac.spec` creates `dist/sage-to-BOC-XML.app` (with the raw binary at `dist/sage-to-BOC-XML`).

Build artifacts land in `dist/`, with intermediate files in `build/`.

Reference: [Packaging PyQt6 applications with PyInstaller](https://www.pythonguis.com/tutorials/packaging-pyqt6-applications-windows-pyinstaller/)

## Project layout

| Path | What it is |
| --- | --- |
| `main.py` | Command-line entry point |
| `gui/boc-gui.py` | PyQt6 desktop app |
| `helpers.py` | Reads and tidies the Sage report |
| `boc_xml.py` | Builds the `pain.001.001.03` XML |
| `pain.001.001.03.xsd` | The XML schema |
| `sample.xlsx` | Example report layout (fake data) |
| `*.spec` | PyInstaller specs for Windows and macOS |
