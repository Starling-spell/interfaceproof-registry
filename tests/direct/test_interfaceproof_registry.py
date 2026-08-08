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
