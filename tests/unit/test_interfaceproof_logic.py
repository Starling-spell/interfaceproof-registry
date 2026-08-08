from pathlib import Path


MODULE_PATH = Path(__file__).parents[2] / "contracts" / "InterfaceProofRegistry.py"
SOURCE = MODULE_PATH.read_text(encoding="utf-8")
# The helper functions before the contract class are pure Python. Loading that
# section keeps these tests fast and independent from a live GenVM runtime.
HELPERS = SOURCE.split("class InterfaceProofRegistry", 1)[0]
HELPERS = HELPERS.replace("from genlayer import *", "")
MODULE = type("Helpers", (), {})()
exec(HELPERS, MODULE.__dict__)


def test_canonical_query_sorts_and_preserves_required_values():
    assert MODULE._canonical_query('{"status":"available","limit":"10"}') == {
        "limit": "10", "status": "available"
    }


def test_operation_path_cannot_contain_an_unbound_query_string():
    assert MODULE._public_https("https://petstore3.swagger.io/api/v3") is True
    assert MODULE._public_https("http://petstore3.swagger.io/api/v3") is False
    assert MODULE._public_https("https://127.0.0.1/openapi.json") is False


def test_public_records_must_match_exactly():
    assert MODULE._same_public({"compatible": True, "probe_status": 200},
                               {"probe_status": 200, "compatible": True}) is True
    assert MODULE._same_public({"compatible": True}, {"compatible": False}) is False
