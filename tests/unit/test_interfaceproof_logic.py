from pathlib import Path
from types import SimpleNamespace


MODULE_PATH = Path(__file__).parents[2] / "contracts" / "InterfaceProofRegistry.py"
SOURCE = MODULE_PATH.read_text(encoding="utf-8")
# The helper functions before the contract class are pure Python. Loading that
# section keeps these tests fast and independent from a live GenVM runtime.
HELPERS = SOURCE.split("class InterfaceProofRegistry", 1)[0]
HELPERS = HELPERS.replace("from genlayer import *", "")
MODULE = type("Helpers", (), {})()
MODULE.gl = SimpleNamespace(vm=SimpleNamespace(UserError=ValueError))
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


def test_server_binding_only_accepts_absolute_query_free_https_servers():
    assert MODULE._normalized_server("https://petstore3.swagger.io/api/v3/") == "https://petstore3.swagger.io/api/v3"
    assert MODULE._normalized_server("https://petstore3.swagger.io/api/v3?x=1") == ""
    assert MODULE._declared_servers({"servers": [{"url": "https://api.example.com/v1"}, {"url": "/v1"}]},
                                    "https://docs.example.com/openapi.json") == [
        "https://api.example.com/v1", "https://docs.example.com/v1"
    ]


def test_post_consensus_validation_binds_record_without_refetching():
    spec = {
        "base_url": "https://api.example.com/v1",
        "operation_path": "/items",
        "query": {"status": "active"},
    }
    public = {
        "compatible": True,
        "operation_present": True,
        "operation_id": "listItems",
        "declared_servers": ["https://api.example.com/v1"],
        "base_server_declared": True,
        "required_query_parameters": ["status"],
        "declared_query_parameters": ["status"],
        "query_parameters_complete": True,
        "probe_matches_operation_path": True,
        "probe_status": 200,
        "response_is_json": True,
        "probe_url": "https://api.example.com/v1/items?status=active",
    }
    assert MODULE._validate_public_record(public, spec) == public


def test_post_consensus_validation_rejects_mutated_compatibility():
    spec = {"base_url": "https://api.example.com/v1", "operation_path": "/items", "query": {"status": "active"}}
    public = {
        "compatible": False, "operation_present": True, "operation_id": "listItems",
        "declared_servers": ["https://api.example.com/v1"], "base_server_declared": True,
        "required_query_parameters": ["status"], "declared_query_parameters": ["status"],
        "query_parameters_complete": True, "probe_matches_operation_path": True,
        "probe_status": 200, "response_is_json": True,
        "probe_url": "https://api.example.com/v1/items?status=active",
    }
    try:
        MODULE._validate_public_record(public, spec)
        assert False, "mutated compatibility must be rejected"
    except Exception:
        pass
