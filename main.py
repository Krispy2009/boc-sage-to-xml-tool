import os
import pdb
import uuid
import datetime
import xml.etree.ElementTree as ET

from pydoc import doc
from turtle import pd

# from pprint import pprint
from openpyxl import load_workbook
from constants import BOC_BIC


def build_grp_hdr(ccti, number_of_txns=0, total=0):
    grp_hdr = ET.SubElement(ccti, "GrpHdr")
    msg_id = ET.SubElement(grp_hdr, "MsgId")
    msg_id.text = str(uuid.uuid4())

    # TODO: Correct format
    dt = ET.SubElement(grp_hdr, "CreDtTm")
    dt.text = str(datetime.datetime.now())

    txns = ET.SubElement(grp_hdr, "NbOfTxs")
    txns.text = str(number_of_txns)

    # Control Sum has 2 decimal places
    control_sum = ET.SubElement(grp_hdr, "CtrlSum")
    control_sum.text = f"{total:.2f}"

    init_party = ET.SubElement(grp_hdr, "InitgPty")
    nm = ET.SubElement(init_party, "Nm")
    nm.text = f"{os.environ['COMPANY_NAME']}"


def build_pmts(ccti, transaction):
    pmt_info = ET.SubElement(ccti, "PmtInf")
    pmt_id = ET.SubElement(pmt_info, "PmtInfId")
    pmt_id.text(uuid.uuid4())

    # Value is always TRF which means Credit Transfer
    pmt_mtd = ET.SubElement(pmt_info, "PmtMtd")
    pmt_mtd.text = "TRF"

    pmt_tp_inf = ET.SubElement(pmt_info, "PmtTpInf")
    service_level = ET.SubElement(pmt_tp_inf, "SvcLvl")
    code = ET.SubElement(service_level, "Cd")
    if transaction.get("BIC") == BOC_BIC:
        code.text = "TBOC"
    else:
        code.text = "SEPA"

    req_ex_date = ET.SubElement(pmt_info, "ReqdExctnDt")
    req_ex_date.text = datetime.datetime.now().strftime("%Y-%m-%D")

    # The only required fields is IBAN, BIC
    # Charges are by default Shared in SEPA and OUR in TBOC transfers
    # TODO: Ask whether this is ok
    debtor = ET.SubElement(pmt_info, "Dbtr")

    debtor_acct = ET.SubElement(pmt_info, "DbtrAcct")
    debtor_id = ET.SubElement(debtor_acct, "Id")
    iban = ET.SubElement(debtor_id, "IBAN")
    iban.text = str(os.environ["COMPANY_IBAN"])

    debtor_agent = ET.SubElement(pmt_info, "DbtrAgt")
    fin_inst = ET.SubElement(debtor_agent, "FinInstnId")
    bic = ET.SubElement(fin_inst, "BIC")
    bic.text = BOC_BIC

    # Not Sure this is needed
    # TODO: Ask about charges (like above)
    chrg_bearer = ET.SubElement(pmt_info, "ChrgBr")
    if transaction.get("BIC") == BOC_BIC:
        chrg_bearer.text = "DEBT"
    else:
        chrg_bearer.text = "SHAR"


def build_xml(transactions):
    document = ET.Element("Document")
    ccti = ET.SubElement(document, "CstmrCdtTrfInitn")

    # Add Group Header
    build_grp_hdr(ccti)

    # One PMT Info element per transaction
    for transaction in transactions:
        build_pmts(ccti)
    ET.dump(document)


def parse_sage_report(filename):
    transactions = []
    wb = load_workbook(filename)
    ws = wb.active

    # Keep unmerging until there are no merged cells
    while len(ws.merged_cells.ranges):
        ws = unmerge_rows(ws)

    for xl_row in ws:
        if xl_row[0].row < 8:
            continue
        transactions.append(xl_row_to_dict(xl_row))
    return transactions


def xl_row_to_dict(xl_row):
    row = {}
    row_map = {
        "B": "name",
        "F": "BIC",
        "H": "IBAN",
        "K": "Currency",
        "L": "Turnover",
        "M": "Balance",
        "N": "Current",
        "O": "Period 1",
        "P": "Period 2",
        "Q": "Period 3",
        "R": "Older",
    }
    for col in xl_row:

        if col.column_letter in row_map:
            row_title = row_map[col.column_letter]
            row[row_title] = col.value
    return row


def unmerge_rows(ws):

    for merged in ws.merged_cells:
        ws.unmerge_cells(str(merged))
    return ws


if __name__ == "__main__":
    transactions = parse_sage_report("sample.xlsx")
    build_xml(transactions)
