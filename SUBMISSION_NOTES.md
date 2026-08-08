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

**Live contract:** https://explorer-studio.genlayer.com/address/0x448D7f288C6EE5f09d9bbB813f7785FdaF181154

**Deployment transaction:** https://explorer-studio.genlayer.com/tx/0x5758eabc2beaaddfaa468775699967a5aa92ab92237fb9dd5c91c1695e457e9e

**Live attestation:** https://explorer-studio.genlayer.com/tx/0x4cc9d763c2dbfa69a7fd091062113dac01a9bab3db361efa3abc3f06305e694c
