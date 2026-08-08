# InterfaceProof Registry

InterfaceProof Registry is a reusable GenLayer primitive for contracts and
agents that depend on public HTTP APIs. It records validator-agreed proof that
an immutable OpenAPI operation revision exists and that its bound live GET probe
returns JSON successfully.

## Why consensus matters

An API consumer should not trust an attester to say an endpoint is compatible.
For each attestation, the leader and every validator independently fetch the
registered OpenAPI document, verify that the registered base URL is an absolute
HTTPS server declared by the document, and execute the probe constructed from
the immutable `base_url + operation_path + canonical query`. They recompute the full public
record and require exact equality. The stored result includes declared-server
binding, operation existence, required query parameters, status, JSON response
check, and explicit operation-path binding.

Two consumer gates are provided:

- `is_compatible(attestation_id)` for a specific immutable proof.
- `is_continuously_compatible(revision_id)` for a revision's latest proof.

The registry never stores a leader-created summary or accepts a format-only
check. It supports public HTTPS GET/JSON API operations; authentication,
write operations, and uptime guarantees are explicitly out of scope.

## Example

Register the Swagger pet-search API with its `status=available` query, then call
`attest_interface`. Consumers can require `is_continuously_compatible` before
depending on the endpoint.

## Validation

```powershell
genvm-lint check contracts\InterfaceProofRegistry.py --json
python -m py_compile contracts\InterfaceProofRegistry.py
```

## StudioNet deployment

The registry is deployed at
[`0x448D7f288C6EE5f09d9bbB813f7785FdaF181154`](https://explorer-studio.genlayer.com/address/0x448D7f288C6EE5f09d9bbB813f7785FdaF181154).
Its [deployment transaction](https://explorer-studio.genlayer.com/tx/0x5758eabc2beaaddfaa468775699967a5aa92ab92237fb9dd5c91c1695e457e9e)
and [live compatible attestation](https://explorer-studio.genlayer.com/tx/0x4cc9d763c2dbfa69a7fd091062113dac01a9bab3db361efa3abc3f06305e694c)
finalized with 3/3 validator agreement and successful executions.
