# StudioNet deployment evidence

## Corrected server-bound deployment

- Date (UTC): 2026-08-08
- Network: GenLayer StudioNet (gasless)
- Contract: `0x448D7f288C6EE5f09d9bbB813f7785FdaF181154`
- Contract Explorer: https://explorer-studio.genlayer.com/address/0x448D7f288C6EE5f09d9bbB813f7785FdaF181154
- Deployment transaction: https://explorer-studio.genlayer.com/tx/0x5758eabc2beaaddfaa468775699967a5aa92ab92237fb9dd5c91c1695e457e9e
- Revision registration: https://explorer-studio.genlayer.com/tx/0xc4289c397e3b306208767ea6aebc4eae1cb9733cf9dd6706ecc844f954163d78
- Live attestation: https://explorer-studio.genlayer.com/tx/0x4cc9d763c2dbfa69a7fd091062113dac01a9bab3db361efa3abc3f06305e694c
- Revision ID: `swagger-pets-available-v3`
- Attestation ID: `swagger-pets-available-v3-1786228597716`
- Policy: `interfaceproof-v3-server-bound`
- Normalized deployed/local SHA-256: `ae105a42856bae8effb0a332dba97a437aad0e3fae4fbb3a53ea5a6622aeefb4`

Both registration and attestation finalized with `MAJORITY_AGREE` (3 agree,
0 disagree), and both recorded executions were `SUCCESS`.

The stored attestation reports `verified=true`, `compatible=true`,
`base_server_declared=true`, `operation_present=true`,
`probe_matches_operation_path=true`, `query_parameters_complete=true`, HTTP
status 200 and a JSON response. The normalized declared server is
`https://petstore3.swagger.io/api/v3`; the operation is `findPetsByStatus`.

Validation before deployment:

```text
genvm-lint check contracts/InterfaceProofRegistry.py --json  # passed, 8 methods
pytest tests/unit -q                                          # 6 passed
pytest tests/direct -q                                        # 1 passed
TypeScript deployment scripts                                 # passed
```

The earlier contract at `0xaD2639c2a9dD38C8B1Ed8dD9d6781545Aa8CF9F7`
and failed attestation `0xe215...` are superseded and must not be submitted.
