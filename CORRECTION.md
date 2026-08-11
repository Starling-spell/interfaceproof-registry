# Frozen GenVM discovery correction

The rejected repository included `tests/unit/test_interfaceproof_logic.py`. That
test read and executed the Python preamble of the deployable contract, so a
repository-wide frozen GenVM scan selected the test as contract-like source and
reported that it contained no contract class.

The correction removes that artifact. Contract behavior remains covered through
the standard direct-mode test in `tests/direct/test_interfaceproof_registry.py`,
which deploys the real contract and exercises registration, independent web
fetches, exact attestation persistence, and both consumer gates.

`npm run check:discovery` now recursively inspects repository Python files and
fails unless `contracts/InterfaceProofRegistry.py` is the sole contract-source
candidate. It also rejects test code that dynamically reads or executes the
contract source. The corrected StudioNet deployment is always created directly
from this file and verified byte-for-byte with `npm run verify:deployment`.
