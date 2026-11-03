import pytest
from openpyxl import Workbook, load_workbook

from helpers import (
    do_calcs,
    parse_sage_report,
    remove_special_chars,
    remove_spaces,
    xl_row_to_dict,
)

from conftest import OPENPYXL_31_PLUS, make_txn

# parse_sage_report mutates ws.merged_cells while iterating it; openpyxl >= 3.1
# raises "RuntimeError: Set changed size during iteration". requirements.txt pins
# 3.0.9, where it works. strict=True: this flips to a failure once the app is fixed.
openpyxl_31_bug = pytest.mark.xfail(
    OPENPYXL_31_PLUS, strict=True, raises=RuntimeError,
    reason="helpers.unmerge_rows mutates merged_cells while iterating (openpyxl>=3.1)",
)


# ---------- remove_spaces ----------

def test_remove_spaces_strips_every_space():
    assert remove_spaces("CY17 0020 0128 0000") == "CY1700200128" + "0000"


def test_remove_spaces_leaves_a_clean_iban_alone():
    assert remove_spaces("CY17002001280000") == "CY17002001280000"


@pytest.mark.parametrize("empty", [None, ""])
def test_remove_spaces_returns_none_for_empty_values(empty):
    assert remove_spaces(empty) is None


# ---------- remove_special_chars ----------

def test_remove_special_chars_removes_disallowed_characters():
    assert remove_special_chars("A&B_Ltd #1") == "ABLtd 1"


@pytest.mark.parametrize("name", ["Smith-Jones (Cyprus) Ltd.", "A/B, Co: 1+1", "Costa's"])
def test_remove_special_chars_keeps_allowed_punctuation(name):
    assert remove_special_chars(name) == name


def test_remove_special_chars_handles_none():
    assert remove_special_chars(None) is None


# ---------- xl_row_to_dict ----------

def _row(values):
    """Build a one-row sheet from {column_letter: value} and return its cells."""
    ws = Workbook().active
    for letter, value in values.items():
        ws[f"{letter}1"] = value
    return ws[1]


def test_xl_row_to_dict_maps_columns_to_field_names():
    row = _row({
        "B": "SUPPLIER ONE", "F": "BCYPCY2N", "H": "IT60 X054 2811", "K": "€",
        "L": 100.0, "M": 90.0, "N": 10.0, "O": 20.0, "P": 30.0, "Q": 40.0, "R": 50.0,
    })
    assert xl_row_to_dict(row) == {
        "name": "SUPPLIER ONE", "BIC": "BCYPCY2N", "IBAN": "IT60X0542811",
        "Currency": "€", "Turnover": 100.0, "Balance": 90.0, "Current": 10.0,
        "Period 1": 20.0, "Period 2": 30.0, "Period 3": 40.0, "Older": 50.0,
    }


def test_xl_row_to_dict_cleans_iban_and_name():
    row = _row({"B": "A&B_Trading", "H": "DE89 3704 0044"})
    result = xl_row_to_dict(row)
    assert result["name"] == "ABTrading"
    assert result["IBAN"] == "DE8937040044"


def test_xl_row_to_dict_ignores_unmapped_columns():
    row = _row({"A": "ignored", "C": "ignored", "H": "DE89", "Z": "ignored"})
    result = xl_row_to_dict(row)
    assert result["IBAN"] == "DE89"
    # every mapped key is always present (None when the cell is empty)
    assert result["name"] is None and result["Older"] is None
    assert "Z" not in result and "ignored" not in result.values()


# ---------- parse_sage_report ----------

@openpyxl_31_bug
def test_parse_sage_report_reads_the_sample(sample_path):
    txns = parse_sage_report(str(sample_path))
    assert [t["name"] for t in txns] == [
        "COMPANY McCOMPANYFACE", "MISTER MISTER", "RICH LTD",
        "BONOBO ELECTRONICS", "SOMETHING  ITALIA",
    ]


@openpyxl_31_bug
def test_parse_sage_report_excludes_totals_and_header_rows(sample_path):
    txns = parse_sage_report(str(sample_path))
    assert len(txns) == 5
    assert all(t.get("IBAN") for t in txns)


@openpyxl_31_bug
def test_parse_sage_report_cleans_ibans_and_reads_amounts(sample_path):
    txns = {t["name"]: t for t in parse_sage_report(str(sample_path))}
    assert all(" " not in t["IBAN"] for t in txns.values())
    rich = txns["RICH LTD"]
    assert (rich["Period 1"], rich["Period 2"], rich["Period 3"], rich["Older"]) == (0, 0, 332, 55)
    assert txns["SOMETHING  ITALIA"]["BIC"] == "BANCA2"


def _sheet_with_rows(tmp_path, rows, merge=None):
    wb = Workbook()
    ws = wb.active
    for r in rows:
        ws.append(r)
    for rng in merge or []:
        ws.merge_cells(rng)
    path = tmp_path / "report.xlsx"
    wb.save(path)
    return str(path)


def _data_row(iban, name="SUPPLIER"):
    # columns A..R: B name, F BIC, H IBAN, K currency, L..R amounts
    row = [None] * 18
    row[1], row[5], row[7], row[10] = name, "BCYPCY2N", iban, "€"
    row[11:18] = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0]
    return row


def test_parse_sage_report_ignores_rows_above_row_8(tmp_path):
    rows = [[None] * 18 for _ in range(7)]
    rows[2] = _data_row("DE89370400440532013000", "TOO EARLY")      # row 3
    rows.append(_data_row("DE89370400440532013000", "ROW EIGHT"))   # row 8
    txns = parse_sage_report(_sheet_with_rows(tmp_path, rows))
    assert [t["name"] for t in txns] == ["ROW EIGHT"]


def test_parse_sage_report_skips_rows_without_iban(tmp_path):
    rows = [[None] * 18 for _ in range(7)]
    rows.append(_data_row(None, "NO IBAN"))
    rows.append(_data_row("DE89370400440532013000", "HAS IBAN"))
    txns = parse_sage_report(_sheet_with_rows(tmp_path, rows))
    assert [t["name"] for t in txns] == ["HAS IBAN"]


@openpyxl_31_bug
def test_parse_sage_report_unmerges_cells_before_reading(tmp_path):
    # Sage exports merge cells; the IBAN lives in the top-left cell of H8:J8.
    rows = [[None] * 18 for _ in range(7)]
    rows.append(_data_row("DE89370400440532013000", "MERGED ROW"))
    path = _sheet_with_rows(tmp_path, rows, merge=["B8:D8", "H8:J8"])
    assert load_workbook(path).active.merged_cells.ranges  # really merged on disk
    txns = parse_sage_report(path)
    assert [(t["name"], t["IBAN"]) for t in txns] == [("MERGED ROW", "DE89370400440532013000")]


# ---------- do_calcs ----------

def test_do_calcs_adds_all_totals():
    (tx,) = do_calcs([make_txn(p1=1.0, p2=2.0, p3=4.0, older=8.0)])
    assert tx["total_p1_p2"] == 3.0
    assert tx["total_p2_p3"] == 6.0
    assert tx["total_p1_p2_p3"] == 7.0
    assert tx["total_p2_p3_older"] == 14.0
    assert tx["total_all"] == 15.0


def test_do_calcs_updates_the_list_in_place_and_returns_it():
    txns = [make_txn(p2=1.0), make_txn(p2=2.0)]
    assert do_calcs(txns) is txns
    assert [t["total_p2_p3_older"] for t in txns] == [1.0, 2.0]


def test_do_calcs_handles_an_empty_list():
    assert do_calcs([]) == []


def test_do_calcs_is_float_arithmetic():
    # Documents current behaviour: totals are binary floats, so callers must
    # round (BoCXML formats with :.2f). Money would be safer as Decimal.
    (tx,) = do_calcs([make_txn(p2=0.1, p3=0.2)])
    assert tx["total_p2_p3"] != 0.3
    assert tx["total_p2_p3"] == pytest.approx(0.3)
