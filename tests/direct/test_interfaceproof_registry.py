import json


def test_attestation_is_persisted_after_consensus(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/InterfaceProofRegistry.py")
    direct_vm.sender = direct_alice
    openapi = {
        "servers": [{"url": "https://api.example.com/v1"}],
        "paths": {
            "/items": {
                "get": {
                    "operationId": "listItems",
                    "parameters": [{"in": "query", "name": "status", "required": True}],
                }
            }
        },
    }
    direct_vm.mock_web(r".*docs\.example\.com/openapi\.json.*", {
        "status": 200, "body": json.dumps(openapi),
    })
    direct_vm.mock_web(r".*api\.example\.com/v1/items\?status=active.*", {
        "status": 200, "body": '[{"id":1}]',
    })
    contract.register_revision(
        "items-v1", "Items API", "https://docs.example.com/openapi.json",
        "https://api.example.com/v1", "/items", "get", '{"status":"active"}',
    )
    result = contract.attest_interface("items-v1", "items-v1-proof")
    stored = contract.get_attestation("items-v1-proof")
    assert result["compatible"] is True
    assert stored["verified"] is True
    assert stored["base_server_declared"] is True
    assert contract.is_compatible("items-v1-proof") is True
    assert contract.is_continuously_compatible("items-v1") is True
    assert contract.is_fresh_and_compatible("items-v1", 0) is True
    assert contract.get_freshness("items-v1")["age_attestations"] == 0


def test_http_failure_is_stored_as_latest_negative(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/InterfaceProofRegistry.py")
    direct_vm.sender = direct_alice
    openapi = {"servers": [{"url": "https://api.example.com/v1"}], "paths": {
        "/items": {"get": {"operationId": "listItems", "parameters": []}}}}
    direct_vm.mock_web(r".*docs\.example\.com/openapi\.json.*", {"status": 200, "body": json.dumps(openapi)})
    direct_vm.mock_web(r".*api\.example\.com/v1/items.*", {"status": 503, "body": "down"})
    contract.register_revision("items-v1", "Items", "https://docs.example.com/openapi.json",
                               "https://api.example.com/v1", "/items", "get", '{"limit":"1"}')
    result = contract.attest_interface("items-v1", "negative-503")
    assert result["verified"] is True
    assert result["compatible"] is False
    assert result["probe_outcome"] == "HTTP_5XX"
    assert result["probe_status"] == 503
    assert contract.get_latest("items-v1")["attestation_id"] == "negative-503"
    assert contract.is_continuously_compatible("items-v1") is False


def test_invalid_json_is_stored_as_negative(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/InterfaceProofRegistry.py")
    direct_vm.sender = direct_alice
    openapi = {"servers": [{"url": "https://api.example.com/v1"}], "paths": {
        "/items": {"get": {"operationId": "listItems", "parameters": []}}}}
    direct_vm.mock_web(r".*docs\.example\.com/openapi\.json.*", {"status": 200, "body": json.dumps(openapi)})
    direct_vm.mock_web(r".*api\.example\.com/v1/items.*", {"status": 200, "body": "not-json"})
    contract.register_revision("items-v1", "Items", "https://docs.example.com/openapi.json",
                               "https://api.example.com/v1", "/items", "get", '{"limit":"1"}')
    result = contract.attest_interface("items-v1", "negative-json")
    assert result["probe_outcome"] == "INVALID_JSON"
    assert result["compatible"] is False


def test_freshness_ages_when_registry_advances(direct_vm, direct_deploy, direct_alice):
    contract = direct_deploy("contracts/InterfaceProofRegistry.py")
    direct_vm.sender = direct_alice
    openapi = {"servers": [{"url": "https://api.example.com/v1"}], "paths": {
        "/items": {"get": {"operationId": "listItems", "parameters": []}}}}
    direct_vm.mock_web(r".*docs\.example\.com/openapi\.json.*", {"status": 200, "body": json.dumps(openapi)})
    direct_vm.mock_web(r".*api\.example\.com/v1/items.*", {"status": 200, "body": "[]"})
    for revision in ["items-v1", "items-v2"]:
        contract.register_revision(revision, revision, "https://docs.example.com/openapi.json",
                                   "https://api.example.com/v1", "/items", "get", '{"limit":"1"}')
    contract.attest_interface("items-v1", "proof-v1")
    contract.attest_interface("items-v2", "proof-v2")
    freshness = contract.get_freshness("items-v1")
    assert freshness["age_attestations"] == 1
    assert contract.is_fresh_and_compatible("items-v1", 0) is False
    assert contract.is_fresh_and_compatible("items-v1", 1) is True
