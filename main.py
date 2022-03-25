import pdb
from turtle import pd
import xml.etree.ElementTree as ET
from openpyxl import load_workbook

def build_xml():
    document = ET.Element('Document')
    ccti = ET.SubElement(document, 'CstmrCdtTrfInitn')
    grp_hdr = ET.SubElement(ccti, 'GrpHdr')


def parse_sage_report(filename):
    transactions = []
    wb = load_workbook(filename)
    ws = wb.active
    import pdb; pdb.set_trace()
    for xl_row in ws:
        
        if xl_row[0].row < 8:
            continue
        transactions.append(xl_row_to_dict(xl_row))
    print(transactions)
            
def xl_row_to_dict(xl_row):
    row = {}
    row_map = {'B': 'name', 'F': 'BIC', 'H': 'IBAN', 'K': 'Currency', 'L':'Turnover', 'M': 'Balance', 'N': 'Current', 'O':'Period 1', 'P': 'Period 2', 'Q': 'Period 3', 'R':'Older'}
    for col in xl_row:
        if col.column_letter in row_map:
            row_title = row_map[col.column_letter]
            row[row_title] = col.value
    return row
        
def unmerge_rows(ws):
    for row in ws:
        if row[0].row > 7:
            for col in row:
                try:
                    ws.unmerge_cells()
                except:
                    pass
            



if __name__ == '__main__':
    parse_sage_report('Report.xlsx')
