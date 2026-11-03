"""Shared fixtures. All data here is fake (the repo's sample report, plus
IBANs from public documentation examples)."""
import os
from pathlib import Path

import openpyxl
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SAMPLE_REPORT = REPO_ROOT / "sample.xlsx"
XSD_PATH = REPO_ROOT / "pain.001.001.03.xsd"

OPENPYXL_31_PLUS = tuple(int(x) for x in openpyxl.__version__.split(".")[:2]) >= (3, 1)

NS = "urn:iso:std:iso:20022:tech:xsd:pain.001.001.03"
NSMAP = {"p": NS}

# Public documentation example IBANs, not real accounts.
FAKE_COMPANY_IBAN = "CY17002001280000001200527600"
FAKE_IT_IBAN = "IT60X0542811101000000123456"
FAKE_DE_IBAN = "DE89370400440532013000"
BOC_BIC = "BCYPCY2N"


@pytest.fixture(autouse=True)
def _no_company_env(monkeypatch):
    """Tests must never depend on the developer's own COMPANY_* variables."""
    monkeypatch.delenv("COMPANY_NAME", raising=False)
    monkeypatch.delenv("COMPANY_IBAN", raising=False)


@pytest.fixture
def sample_path():
    assert SAMPLE_REPORT.exists()
    return SAMPLE_REPORT


@pytest.fixture
def company():
    return {"company_name": "FAKE TRADING LTD", "company_iban": FAKE_COMPANY_IBAN}


def make_txn(name="SUPPLIER ONE", bic=BOC_BIC, iban=FAKE_IT_IBAN,
             p1=0.0, p2=0.0, p3=0.0, older=0.0, **extra):
    """A transaction dict as produced by parse_sage_report (before do_calcs)."""
    txn = {
        "name": name, "BIC": bic, "IBAN": iban, "Currency": "€",
        "Turnover": 0.0, "Balance": 0.0, "Current": 0.0,
        "Period 1": p1, "Period 2": p2, "Period 3": p3, "Older": older,
    }
    txn.update(extra)
    return txn


@pytest.fixture
def txn_factory():
    return make_txn
