# StudioNet deployment evidence

## Corrected server-bound deployment

- Date (UTC): 2026-08-11
- Network: GenLayer StudioNet (gasless)
- Contract: `0xD83D8f30c2efc52929F6Ae0460B64C2e9D0479e3`
- Contract Explorer: https://explorer-studio.genlayer.com/address/0xD83D8f30c2efc52929F6Ae0460B64C2e9D0479e3
- Deployment transaction: https://explorer-studio.genlayer.com/tx/0xc20ebc258c2cf1c9d7182a781d4ed866b755e50b6d95a938bf585f1d36e056cf
- Revision registration: https://explorer-studio.genlayer.com/tx/0xfdd2b0e37d584201b64c2bd1071627208e4ea90bf4bfec23cfb811069117ffd0
- Live attestation: https://explorer-studio.genlayer.com/tx/0xd032f0ac9513b6d37cbe5ed133fb1277cd098ed7077b7e0ad3ebd5a13be8bf8f
- Revision ID: `swagger-pets-available-v3`
- Attestation ID: `swagger-pets-available-v3-1786478251726`
- Policy: `interfaceproof-v3-server-bound`
- Normalized deployed/local SHA-256: `ae105a42856bae8effb0a332dba97a437aad0e3fae4fbb3a53ea5a6622aeefb4`

Registration and attestation finalized with `MAJORITY_AGREE` (3 agree,
0 disagree). A direct state read confirms that the attestation is stored and
the continuous-compatibility gate returns `true`.

The stored attestation reports `verified=true`, `compatible=true`,
`base_server_declared=true`, `operation_present=true`,
`probe_matches_operation_path=true`, `query_parameters_complete=true`, HTTP
status 200 and a JSON response. The normalized declared server is
`https://petstore3.swagger.io/api/v3`; the operation is `findPetsByStatus`.

Validation before deployment:

```text
genvm-lint check contracts/InterfaceProofRegistry.py --json  # passed, 8 methods
pytest tests/direct -q                                        # 1 passed
npm run check:discovery                                       # sole candidate passed
npm run typecheck                                             # passed
```

All earlier contracts and transactions are superseded and must not be submitted.
