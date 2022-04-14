from boc_xml import BoCXML
from helpers import parse_sage_report, do_calcs

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from api import handlers

app = FastAPI()


@app.get("/", response_class=HTMLResponse)
async def root():
    return await handlers.root()


if __name__ == "__main__":
    transactions = parse_sage_report("sample.xlsx")
    transactions = do_calcs(transactions)

    boc_xml = BoCXML(transactions)

    boc_xml.build_xml(transactions)
