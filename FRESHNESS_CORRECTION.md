# Steward correction: negative outcomes and freshness

The v4 contract makes the bound live probe a total consensus function. A 4xx,
5xx, request failure, or invalid JSON response becomes a bounded negative
attestation rather than an exception. The leader cannot choose this status:
validators repeat the same bound request and compare the complete normalized
record exactly.

Every finalized attestation receives a monotonically increasing registry
sequence. The latest sequence is stored per revision, including for negative
results. Therefore a new negative result replaces an older positive latest
result and immediately closes `is_continuously_compatible`.

Consumers that need explicit freshness call
`is_fresh_and_compatible(revision_id, max_age_attestations)`. Age is measured as
the number of registry attestations finalized since that revision's latest
result and is also inspectable through `get_freshness`.

See `DEPLOYMENT_EVIDENCE.md` for source-matched deployment and a live stored
HTTP 500 negative attestation.
