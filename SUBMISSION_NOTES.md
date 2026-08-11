# Submission notes

**Title:** InterfaceProof Registry - Consensus-Verified API Compatibility

**Purpose:** A reusable GenLayer primitive that lets downstream contracts and
agents gate actions on a consensus-verified public API operation. Revision
creators register an immutable OpenAPI URL, a query-free HTTPS base URL that
must be declared by the document, an operation path/method and canonical query
parameters. Attestations bind the live probe to that exact operation.

**Consensus:** Validators independently re-fetch the OpenAPI document and call
the immutable bound probe. They derive operation identity, declared server,
required query parameters, full probe path, HTTP result and JSON status;
consensus requires exact equality of the entire public record. A deterministic
post-consensus invariant check binds all stored fields without another web
request. `is_compatible` and `is_continuously_compatible` are composable gates.

**Limits:** Public HTTPS GET/JSON interfaces only. This proves point-in-time
compatibility, not credentials, write behavior or continuous availability.

**Correction:** Removed the contract-source-executing unit helper that frozen
GenVM discovery selected incorrectly. The repository guard now proves the
deployable contract is the sole contract-source candidate.

**Live contract:** https://explorer-studio.genlayer.com/address/0xD83D8f30c2efc52929F6Ae0460B64C2e9D0479e3

**Deployment transaction:** https://explorer-studio.genlayer.com/tx/0xc20ebc258c2cf1c9d7182a781d4ed866b755e50b6d95a938bf585f1d36e056cf

**Revision registration:** https://explorer-studio.genlayer.com/tx/0xfdd2b0e37d584201b64c2bd1071627208e4ea90bf4bfec23cfb811069117ffd0

**Live attestation:** https://explorer-studio.genlayer.com/tx/0xd032f0ac9513b6d37cbe5ed133fb1277cd098ed7077b7e0ad3ebd5a13be8bf8f
