from boc_xml import BoCXML
from helpers import parse_sage_report, do_calcs


if __name__ == "__main__":
    transactions = parse_sage_report("Report.xlsx")
    transactions = do_calcs(transactions)

    boc_xml = BoCXML(transactions)

    boc_xml.build_xml(transactions)
