import datetime
import sys

from boc_xml import BoCXML
from helpers import parse_sage_report, do_calcs


if __name__ == "__main__":
    # Optional execution date as YYYY-MM-DD, e.g. `python main.py 2026-07-01`.
    # Defaults to today when omitted.
    execution_date = None
    if len(sys.argv) > 1:
        execution_date = datetime.datetime.strptime(sys.argv[1], "%Y-%m-%d").date()

    transactions = parse_sage_report("Report.xlsx")
    transactions = do_calcs(transactions)

    boc_xml = BoCXML(transactions, execution_date=execution_date)

    boc_xml.build_xml(transactions)
