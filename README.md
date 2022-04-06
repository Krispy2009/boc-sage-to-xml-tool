# boc-sage-to-xml-tool
A tool to convert a Sage report to Bank Of Cyprus xml format for multiple payments

This tool is still in its early stages, but I have used for my own use successfully. 
It is tailored to what I need at the moment but feel free to open an issue or PR to discuss any changes you need.


## How to run
1. Install requirements `pip install -r requirements.txt`
2. Make sure you have a sage report in the current directory (see sample.xlsx)
3. Make sure you have the following env variables exported (I use [direnv](https://direnv.net/) to manage my env variables in a .env file):
```
COMPANY_NAME=<your company name>
COMPANY_IBAN=<your company IBAN>
```
4. Make sure the filename in `main.py` corresponds to your report's filename.
5. Run `python main.py`
6. 🎉 the XML should be created in the current directory.


