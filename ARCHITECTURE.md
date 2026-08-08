# Architecture and invariants

`register_revision` stores one immutable API dependency declaration. Its probe
is not supplied at attestation time: `attest_interface` deterministically builds
the only allowed probe from the stored base URL, operation path and canonical
query map.

For every attestation, both the leader and validators independently:

1. Fetch the registered OpenAPI document and locate the exact GET operation.
2. Derive its required query parameters from the document.
3. Fetch only the bound live probe URL.
4. Recompute a canonical public record.

The validator accepts only byte-for-byte equal canonical public records. The
stored record includes the operation result, required and declared query
parameters, path-binding boolean, HTTP status and JSON response check. This
binds every consumer-facing gate to independently re-fetched evidence rather
than a leader claim.

The registry does not promise API uptime; it records immutable point-in-time
compatibility attestations. Consumers choose whether an older proof is adequate
or call `is_continuously_compatible` after requesting newer attestations.
