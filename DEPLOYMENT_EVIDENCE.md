# StudioNet deployment evidence

- Date (UTC): 2026-08-08
- Network: GenLayer StudioNet (gasless)
- Deployer: `0x614768bCA33e1D7bc324d11A347c73F39a4CC585` (ephemeral SDK account)
- Contract: `0xaD2639c2a9dD38C8B1Ed8dD9d6781545Aa8CF9F7`
- Contract Explorer: https://explorer-studio.genlayer.com/address/0xaD2639c2a9dD38C8B1Ed8dD9d6781545Aa8CF9F7
- Deployment transaction: https://explorer-studio.genlayer.com/tx/0x226e14ef3d1a91c570f298e760d566558896b21ff5256cc7e5babda456a1a04d
- Deployment result: finalized successfully by the StudioNet SDK receipt wait.

Validation before deployment:

```text
python -m py_compile contracts/InterfaceProofRegistry.py  # passed
genvm-lint check contracts/InterfaceProofRegistry.py --json  # passed: 8 methods (6 view, 2 write)
pytest tests/unit -q  # 3 passed
```

Limitation: this evidence proves deployment only. A separate transaction must
register a public API revision and finalize an attestation before claiming a
live compatibility result.
