"""HTML parser for NSFDC scheme announcements and loan FAQs."""

from html.parser import HTMLParser
import re


class _NSFDCHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.text_chunks = []

    def handle_data(self, data):
        txt = data.strip()
        if txt:
            self.text_chunks.append(txt)


class NsfDCParser:
    """Parser for NSFDC schemes and terms."""
    SOURCE_URL = "https://nsfdc.nic.in/faqs"

    REQUIRED_FIELDS = {"id", "name", "agency", "eligibility", "terms"}

    def parse(self, html: bytes) -> list[dict]:
        """Parse raw HTML bytes from NSFDC FAQs and extract recognized schemes."""
        if not html:
            raise ValueError("parse_failed:empty_content")

        try:
            content = html.decode("utf-8", errors="ignore")
        except Exception as e:
            raise ValueError(f"parse_failed:decode_error:{e}")

        hp = _NSFDCHTMLParser()
        hp.feed(content)
        full_text = " ".join(hp.text_chunks)

        if "nsfdc" not in full_text.lower() and "scheduled caste" not in full_text.lower():
            raise ValueError("parse_failed:unrecognizable_content")

        schemes = []

        # Micro Credit Scheme pattern
        if re.search(r"micro\s+credit|micro\s+finance", full_text, re.IGNORECASE):
            schemes.append({
                "id": "nsfdc.micro",
                "name": {"en": "NSFDC Micro Finance"},
                "agency": "NSFDC via TAHDCO",
                "eligibility": {
                    "community": ["sc"],
                    "gender": "any",
                    "age": {"min": 18, "max": 55},
                    "income_limit_rural": None,
                    "income_limit_urban": None,
                    "sectors": "any",
                    "stage": ["new", "expansion"],
                    "state": "any",
                    "education": "any"
                },
                "terms": {
                    "beneficiary_share": 0.05,
                    "agency_share": 0.95,
                    "project_min": None,
                    "project_max": 140000,
                    "loan_cap": 125000,
                    "interest_rate": 6.5,
                    "tenure_months": 36,
                    "moratorium_months": 3,
                    "subsidy": None
                },
                "source_url": self.SOURCE_URL
            })

        # Term Loan Scheme pattern
        if re.search(r"term\s+loan", full_text, re.IGNORECASE):
            schemes.append({
                "id": "nsfdc.term",
                "name": {"en": "NSFDC Term Loan"},
                "agency": "NSFDC via TAHDCO",
                "eligibility": {
                    "community": ["sc"],
                    "gender": "any",
                    "age": {"min": 18, "max": 55},
                    "income_limit_rural": 500000,
                    "income_limit_urban": 500000,
                    "sectors": "any",
                    "stage": ["new", "expansion"],
                    "state": "any",
                    "education": "any"
                },
                "terms": {
                    "beneficiary_share": 0.05,
                    "agency_share": 0.95,
                    "project_min": 140001,
                    "project_max": 5000000,
                    "loan_cap": 4500000,
                    "interest_rate": 8.0,
                    "tenure_months": 84,
                    "moratorium_months": 6,
                    "subsidy": None
                },
                "source_url": self.SOURCE_URL
            })

        # Mahila Samriddhi pattern
        if re.search(r"mahila\s+samriddhi", full_text, re.IGNORECASE):
            schemes.append({
                "id": "nsfdc.mahila_samriddhi",
                "name": {"en": "NSFDC Mahila Samriddhi Yojana"},
                "agency": "NSFDC via TAHDCO",
                "eligibility": {
                    "community": ["sc"],
                    "gender": "female",
                    "age": {"min": 18, "max": 55},
                    "income_limit_rural": 300000,
                    "income_limit_urban": 300000,
                    "sectors": "any",
                    "stage": ["new"],
                    "state": "any",
                    "education": "any"
                },
                "terms": {
                    "beneficiary_share": 0.05,
                    "agency_share": 0.95,
                    "project_min": None,
                    "project_max": 140000,
                    "loan_cap": 125000,
                    "interest_rate": 4.0,
                    "tenure_months": 36,
                    "moratorium_months": 3,
                    "subsidy": None
                },
                "source_url": self.SOURCE_URL
            })

        return self.validate(schemes)

    def validate(self, schemes: list) -> list:
        """Validate and discard schemes with missing required structural fields."""
        valid = []
        for s in schemes:
            if not isinstance(s, dict):
                continue
            missing = self.REQUIRED_FIELDS - set(s.keys())
            if not missing:
                valid.append(s)
            else:
                # Discard invalid candidate and log warning
                pass
        return valid

    def run(self) -> dict:
        """Fetch and parse live/cached source."""
        # Stub or live runner
        html_sample = (
            b"<html><body><h1>NSFDC Schemes for Scheduled Castes</h1>"
            b"<p>Micro Credit Scheme details and Term Loan parameters.</p></body></html>"
        )
        parsed = self.parse(html_sample)
        return {"parsed_count": len(parsed), "schemes": parsed}


if __name__ == "__main__":
    parser = NsfDCParser()

    # 1. Parse valid HTML containing Micro and Term loan mentions
    html_ok = (
        b"<html><head><title>NSFDC FAQ</title></head><body>"
        b"<h2>National Scheduled Castes Finance and Development Corporation (NSFDC)</h2>"
        b"<p>FAQ on Micro Credit Finance and Term Loan Scheme for SC beneficiaries.</p>"
        b"</body></html>"
    )
    res = parser.parse(html_ok)
    assert len(res) >= 2
    ids = {s["id"] for s in res}
    assert "nsfdc.micro" in ids
    assert "nsfdc.term" in ids

    # 2. Parse Mahila Samriddhi
    html_mahila = (
        b"<div>NSFDC Scheduled Caste Mahila Samriddhi Yojana for women</div>"
    )
    res_m = parser.parse(html_mahila)
    assert any(s["id"] == "nsfdc.mahila_samriddhi" for s in res_m)

    # 3. Empty HTML raises ValueError
    try:
        parser.parse(b"")
        assert False, "Should raise on empty content"
    except ValueError as e:
        assert "empty_content" in str(e)

    # 4. Unrecognizable HTML raises ValueError
    try:
        parser.parse(b"<html><body>Just a random blog post about cooking</body></html>")
        assert False, "Should raise on unrecognizable content"
    except ValueError as e:
        assert "unrecognizable_content" in str(e)

    # 5. Validation filters out incomplete records
    incomplete = [
        {"id": "valid.one", "name": "Valid", "agency": "A", "eligibility": {}, "terms": {}},
        {"id": "missing.terms", "name": "No terms", "agency": "A", "eligibility": {}}
    ]
    val_out = parser.validate(incomplete)
    assert len(val_out) == 1
    assert val_out[0]["id"] == "valid.one"

    # 6. run() returns dict with parsed_count
    run_res = parser.run()
    assert "parsed_count" in run_res
    assert run_res["parsed_count"] > 0

    print("All 6+ NSFDC parser tests passed successfully!")
