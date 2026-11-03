import datetime
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

import pytest

from boc_xml import BoCXML
from constants import BOC_BIC
from helpers import do_calcs, parse_sage_report

from conftest import (
    FAKE_COMPANY_IBAN, FAKE_DE_IBAN, FAKE_IT_IBAN, NSMAP, OPENPYXL_31_PLUS,
    REPO_ROOT, SAMPLE_REPORT, XSD_PATH, make_txn,
)

FILENAME_RE = re.compile(r"^\d{8}_\d{6}_.+\.xml$")  # suffix is hardcoded "ACMA"; don't assert it


def build(tmp_path, txns, company, **kw):
    """Run BoCXML into tmp_path and return (instance, parsed root)."""
    bx = BoCXML(do_calcs(txns), output_dir=str(tmp_path), **company, **kw)
    # NB: the constructor overwrites self.document with build_xml's return
    # value, i.e. the written file's path (see test below).
    return bx, ET.parse(bx.document).getroot()


def q(node, path):
    return node.findall(path, NSMAP)


def amounts(root):
    return [e.text for e in q(root, ".//p:InstdAmt")]


# ---------- configuration ----------

def test_missing_company_details_raise(tmp_path):
    with pytest.raises(Exception, match="COMPANY_NAME and COMPANY_IBAN"):
        BoCXML([], output_dir=str(tmp_path))


def test_only_one_company_value_is_not_enough(tmp_path):
    with pytest.raises(Exception, match="COMPANY_NAME"):
        BoCXML([], company_name="X", output_dir=str(tmp_path))


def test_company_details_fall_back_to_environment(tmp_path, monkeypatch):
    monkeypatch.setenv("COMPANY_NAME", "ENV CO")
    monkeypatch.setenv("COMPANY_IBAN", FAKE_COMPANY_IBAN)
    root = ET.parse(BoCXML(do_calcs([make_txn(p2=1.0)]), output_dir=str(tmp_path)).document).getroot()
    assert q(root, ".//p:InitgPty/p:Nm")[0].text == "ENV CO"
    assert q(root, ".//p:DbtrAcct//p:IBAN")[0].text == FAKE_COMPANY_IBAN


def test_explicit_company_details_beat_environment(tmp_path, monkeypatch, company):
    monkeypatch.setenv("COMPANY_NAME", "ENV CO")
    monkeypatch.setenv("COMPANY_IBAN", "CY00ENV")
    _, root = build(tmp_path, [make_txn(p2=1.0)], company)
    assert q(root, ".//p:InitgPty/p:Nm")[0].text == "FAKE TRADING LTD"


# ---------- output file ----------

def test_constructor_writes_one_timestamped_file(tmp_path, company):
    build(tmp_path, [make_txn(p2=1.0)], company)
    files = list(tmp_path.iterdir())
    assert len(files) == 1 and FILENAME_RE.match(files[0].name)


def test_document_attribute_holds_the_filepath_not_the_tree(tmp_path, company):
    # Documents a quirk: __init__ does `self.document = self.build_xml(...)`,
    # replacing the Element that build_xml stored with the returned path.
    bx, _ = build(tmp_path, [make_txn(p2=1.0)], company)
    assert isinstance(bx.document, str) and bx.document.endswith(".xml")


def test_calling_build_xml_again_writes_again(tmp_path, company):
    # main.py does exactly this (constructor already built once, then build_xml).
    txns = do_calcs([make_txn(p2=1.0)])
    bx = BoCXML(txns, output_dir=str(tmp_path), **company)
    second = bx.build_xml(txns)
    assert second.startswith(str(tmp_path))
    assert 1 <= len(list(tmp_path.iterdir())) <= 2  # 1 if same second, else 2


# ---------- group header ----------

def test_group_header_fields(tmp_path, company):
    txns = [make_txn(p2=10.0, p3=5.0), make_txn(name="TWO", older=2.5)]
    before = datetime.datetime.now().replace(microsecond=0)
    _, root = build(tmp_path, txns, company)
    after = datetime.datetime.now()
    hdr = q(root, ".//p:GrpHdr")[0]
    assert q(hdr, "p:NbOfTxs")[0].text == "2"
    assert q(hdr, "p:CtrlSum")[0].text == "17.50"
    assert q(hdr, "p:InitgPty/p:Nm")[0].text == "FAKE TRADING LTD"
    assert re.fullmatch(r"[0-9a-f]{32}", q(hdr, "p:MsgId")[0].text)
    created = datetime.datetime.strptime(q(hdr, "p:CreDtTm")[0].text, "%Y-%m-%dT%H:%M:%S")
    assert before <= created <= after


def test_message_ids_are_unique(tmp_path, company):
    _, a = build(tmp_path, [make_txn(p2=1.0)], company)
    _, b = build(tmp_path, [make_txn(p2=1.0)], company)
    assert q(a, ".//p:MsgId")[0].text != q(b, ".//p:MsgId")[0].text


# ---------- payments ----------

def test_one_payment_info_block_per_transaction(tmp_path, company):
    _, root = build(tmp_path, [make_txn(p2=1.0), make_txn(name="B", p3=2.0)], company)
    assert len(q(root, ".//p:PmtInf")) == 2


def test_amount_is_older_plus_p2_plus_p3_and_ignores_p1_and_current(tmp_path, company):
    txn = make_txn(p1=1000.0, p2=10.0, p3=20.0, older=30.0, Current=500.0)
    _, root = build(tmp_path, [txn], company)
    assert amounts(root) == ["60.00"]  # Period 1 is intentionally excluded (open TODO in app)
    assert q(root, ".//p:InstdAmt")[0].get("Ccy") == "EUR"


def test_amounts_always_have_two_decimals(tmp_path, company):
    _, root = build(tmp_path, [make_txn(p2=7.0), make_txn(p2=0.1, p3=0.2)], company)
    assert amounts(root) == ["7.00", "0.30"]


def test_execution_date_is_used(tmp_path, company):
    when = datetime.date.today() + datetime.timedelta(days=30)
    _, root = build(tmp_path, [make_txn(p2=1.0)], company, execution_date=when)
    assert q(root, ".//p:ReqdExctnDt")[0].text == when.isoformat()


def test_execution_date_defaults_to_today(tmp_path, company):
    _, root = build(tmp_path, [make_txn(p2=1.0)], company)
    assert q(root, ".//p:ReqdExctnDt")[0].text == datetime.date.today().isoformat()


def test_debtor_is_the_company_account_at_boc(tmp_path, company):
    _, root = build(tmp_path, [make_txn(p2=1.0)], company)
    assert q(root, ".//p:DbtrAcct//p:IBAN")[0].text == FAKE_COMPANY_IBAN
    assert q(root, ".//p:DbtrAgt//p:BIC")[0].text == BOC_BIC
    assert q(root, ".//p:PmtMtd")[0].text == "TRF"


def test_boc_creditor_gets_tboc_and_debtor_charges(tmp_path, company):
    _, root = build(tmp_path, [make_txn(bic=BOC_BIC, p2=1.0)], company)
    assert q(root, ".//p:SvcLvl/p:Cd")[0].text == "TBOC"
    assert q(root, ".//p:ChrgBr")[0].text == "DEBT"


def test_other_bank_creditor_gets_sepa_and_shared_charges(tmp_path, company):
    _, root = build(tmp_path, [make_txn(bic="BANCA2", iban=FAKE_IT_IBAN, p2=1.0)], company)
    assert q(root, ".//p:SvcLvl/p:Cd")[0].text == "SEPA"
    assert q(root, ".//p:ChrgBr")[0].text == "SHAR"
    assert q(root, ".//p:CdtrAcct//p:IBAN")[0].text == FAKE_IT_IBAN


def test_creditor_name_truncated_to_34_chars(tmp_path, company):
    _, root = build(tmp_path, [make_txn(name="X" * 50, p2=1.0)], company)
    assert q(root, ".//p:Cdtr/p:Nm")[0].text == "X" * 34


def test_end_to_end_ids_are_unique_per_payment(tmp_path, company):
    _, root = build(tmp_path, [make_txn(p2=1.0), make_txn(p2=2.0)], company)
    ids = [e.text for e in q(root, ".//p:EndToEndId")]
    assert len(set(ids)) == 2


def test_payment_without_iban_is_skipped(tmp_path, company):
    txns = [make_txn(p2=1.0, iban=None), make_txn(name="OK", p2=2.0, iban=FAKE_DE_IBAN)]
    _, root = build(tmp_path, txns, company)
    assert amounts(root) == ["2.00"]


def test_remittance_info_only_when_notes_present(tmp_path, company):
    txns = [make_txn(p2=1.0, notes="INV-42"), make_txn(name="B", p2=2.0)]
    _, root = build(tmp_path, txns, company)
    assert [e.text for e in q(root, ".//p:RmtInf/p:Ustrd")] == ["INV-42"]


# ---------- known gaps (xfail strict: they flip to failures once fixed) ----------

@pytest.mark.xfail(strict=True, reason=(
    "MONEY: the zero-amount guard in build_pmts checks transaction['Amt'], a key "
    "nothing ever sets, so suppliers owed 0.00 are still emitted as 0.00 payments."))
def test_zero_amount_payments_are_skipped(tmp_path, company):
    _, root = build(tmp_path, [make_txn(p1=56.19), make_txn(name="B", p2=5.0)], company)
    assert amounts(root) == ["5.00"]


@pytest.mark.xfail(strict=True, reason=(
    "MONEY: NbOfTxs is len(input) even when build_pmts skips a transaction, so the "
    "header can claim more payments than the file contains (latent: the parser "
    "already drops rows without an IBAN)."))
def test_nb_of_txs_matches_payments_actually_written(tmp_path, company):
    txns = [make_txn(p2=1.0, iban=None), make_txn(name="B", p2=2.0)]
    _, root = build(tmp_path, txns, company)
    assert int(q(root, ".//p:NbOfTxs")[0].text) == len(q(root, ".//p:PmtInf"))


@pytest.mark.xfail(strict=True, reason=(
    "MONEY: CtrlSum is the float sum of unrounded values, each InstdAmt is rounded "
    "separately, so sub-cent inputs can make CtrlSum != sum(InstdAmt) and the bank "
    "may reject the file. Latent for 2dp Sage data."))
def test_control_sum_equals_sum_of_written_amounts(tmp_path, company):
    txns = [make_txn(p2=0.004), make_txn(name="B", p2=0.004), make_txn(name="C", p2=0.004)]
    _, root = build(tmp_path, txns, company)
    written = sum(float(a) for a in amounts(root))
    assert float(q(root, ".//p:CtrlSum")[0].text) == pytest.approx(written, abs=0.0001)


# ---------- schema validation & the real sample ----------

def _validator():
    etree = pytest.importorskip("lxml.etree")
    if not XSD_PATH.exists():
        pytest.skip("XSD not in repo")
    return etree, etree.XMLSchema(etree.parse(str(XSD_PATH)))


def test_output_validates_against_the_pain_001_001_03_schema(tmp_path, company):
    etree, schema = _validator()
    txns = [make_txn(bic=BOC_BIC, p2=10.0, iban=FAKE_COMPANY_IBAN),
            make_txn(name="DE", bic="COBADEFF", iban=FAKE_DE_IBAN, p3=4.25, older=1.0)]
    bx, _ = build(tmp_path, txns, company)
    doc = etree.parse(bx.document)
    assert schema.validate(doc), schema.error_log


@pytest.mark.xfail(OPENPYXL_31_PLUS, strict=True, raises=RuntimeError,
                   reason="parse_sage_report breaks on openpyxl>=3.1 (see test_helpers)")
def test_sample_report_end_to_end(tmp_path, company):
    txns = do_calcs(parse_sage_report(str(SAMPLE_REPORT)))
    bx = BoCXML(txns, output_dir=str(tmp_path), **company)
    root = ET.parse(bx.document).getroot()
    assert q(root, ".//p:NbOfTxs")[0].text == "5"
    assert q(root, ".//p:CtrlSum")[0].text == "759.24"
    # BONOBO (only Period 1 owed) is listed with 0.00 -- see the zero-amount xfail above.
    assert sorted(amounts(root)) == sorted(["120.00", "45.00", "387.00", "0.00", "207.24"])
    assert sum(float(a) for a in amounts(root)) == pytest.approx(759.24)
    etree, schema = _validator()
    assert schema.validate(etree.parse(bx.document)), schema.error_log


@pytest.mark.xfail(OPENPYXL_31_PLUS, strict=True,
                   reason="main.py -> parse_sage_report breaks on openpyxl>=3.1")
def test_cli_smoke(tmp_path):
    (tmp_path / "Report.xlsx").write_bytes(SAMPLE_REPORT.read_bytes())
    env = {"PATH": "/usr/bin:/bin", "COMPANY_NAME": "FAKE TRADING LTD",
           "COMPANY_IBAN": FAKE_COMPANY_IBAN, "PYTHONPATH": str(REPO_ROOT)}
    res = subprocess.run([sys.executable, str(REPO_ROOT / "main.py"), "2030-01-31"],
                         cwd=tmp_path, env=env, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    xmls = list(tmp_path.glob("*.xml"))
    assert 1 <= len(xmls) <= 2  # double build: constructor + build_xml
    root = ET.parse(xmls[0]).getroot()
    assert q(root, ".//p:ReqdExctnDt")[0].text == "2030-01-31"
