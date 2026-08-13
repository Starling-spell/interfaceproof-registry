# StudioNet deployment evidence

## Negative-outcome and freshness correction (v4)

- Date (UTC): 2026-08-13
- Network: GenLayer StudioNet
- Contract: `0x42f92b52eE2568c0e5dE70d7e1eD63159eb01a15`
- Contract Explorer: https://explorer-studio.genlayer.com/address/0x42f92b52eE2568c0e5dE70d7e1eD63159eb01a15
- Deployment transaction: https://explorer-studio.genlayer.com/tx/0xe2c09b54f16ad0db411258cd390a366e0bf01ed75b1d327260b677bd797dfbb6
- Revision registration: https://explorer-studio.genlayer.com/tx/0xb4def5bb6ceea283f5bc2f651d493e403d59660154c03ca942bb0963775a638d
- Consensus-verified negative attestation: https://explorer-studio.genlayer.com/tx/0x94060797c0133b842323bac011c5c8da02bf8c32d280c563b185f2d78cfd2b5e
- Revision ID: `swagger-pets-available-v3`
- Policy: `interfaceproof-v4-negative-freshness`
- Exact deployed/local SHA-256: `5e55b2dae61d57df3b0aa203eb07f75dbfa44b61fc1a2ac4e624ac65236a3055`

The live endpoint returned HTTP 500. The attestation did not abort: it finalized
with `MAJORITY_AGREE` and stored an exact, validator-recomputed negative record:
`verified=true`, `compatible=false`, `probe_outcome=HTTP_5XX`,
`probe_status=500`, and `attestation_sequence=1`. It became the revision's
latest result, so both compatibility gates return false and cannot preserve an
older positive result.

The total probe outcome enum is `OK_JSON`, `HTTP_4XX`, `HTTP_5XX`,
`REQUEST_FAILED`, or `INVALID_JSON`. Validators compare the entire record
exactly. `get_freshness` exposes the latest attestation sequence, current
registry sequence, and their age. `is_fresh_and_compatible` requires both a
positive latest record and an explicit caller-selected maximum age.

Validation before deployment:

```text
GenVM check                         PASS (10 methods)
direct-mode tests                  4 passed
contract-source discovery          PASS (sole deployable candidate)
TypeScript check                   PASS
deployed/local source verification PASS
```

All earlier deployments are superseded and must not be submitted.
