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
pytest tests\direct -q
npm run check:discovery
npm run typecheck
```

## StudioNet deployment

The registry is deployed at
[`0xD83D8f30c2efc52929F6Ae0460B64C2e9D0479e3`](https://explorer-studio.genlayer.com/address/0xD83D8f30c2efc52929F6Ae0460B64C2e9D0479e3).
Its [deployment transaction](https://explorer-studio.genlayer.com/tx/0xc20ebc258c2cf1c9d7182a781d4ed866b755e50b6d95a938bf585f1d36e056cf),
[revision registration](https://explorer-studio.genlayer.com/tx/0xfdd2b0e37d584201b64c2bd1071627208e4ea90bf4bfec23cfb811069117ffd0),
and [latest stored compatible attestation](https://explorer-studio.genlayer.com/tx/0xd032f0ac9513b6d37cbe5ed133fb1277cd098ed7077b7e0ad3ebd5a13be8bf8f)
are the post-correction evidence. See [CORRECTION.md](CORRECTION.md) for the
frozen-review remediation.
