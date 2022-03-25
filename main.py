import pdb
from pydoc import doc
from turtle import pd
import xml.etree.ElementTree as ET
from openpyxl import load_workbook

def build_xml(transactions):
    document = ET.Element('Document')
    ccti = ET.SubElement(document, 'CstmrCdtTrfInitn')
    grp_hdr = ET.SubElement(ccti, 'GrpHdr')

    ET.dump(document)


def parse_sage_report(filename):
    transactions = []
    wb = load_workbook(filename)
    ws = wb.active
    

    while len(ws.merged_cells.ranges):
        ws = unmerge_rows(ws)

    for xl_row in ws:
        if xl_row[0].row < 8:
            continue


        transactions.append(xl_row_to_dict(xl_row))
    return transactions

def xl_row_to_dict(xl_row):
    row = {}
    row_map = {'B': 'name', 'F': 'BIC', 'H': 'IBAN', 'K': 'Currency', 'L':'Turnover', 'M': 'Balance', 'N': 'Current', 'O':'Period 1', 'P': 'Period 2', 'Q': 'Period 3', 'R':'Older'}
    for col in xl_row:

        if col.column_letter in row_map:
            row_title = row_map[col.column_letter]
            row[row_title] = col.value
    return row
        
def unmerge_rows(ws):
    
    for merged in ws.merged_cells:
        ws.unmerge_cells(str(merged))
    return ws
            



if __name__ == '__main__':
    transactions = parse_sage_report('Report_small.xlsx')
    build_xml(transactions)

