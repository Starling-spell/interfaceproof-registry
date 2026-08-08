# Submission notes

**Title:** InterfaceProof Registry — Consensus-Verified API Compatibility

**Purpose:** A reusable GenLayer primitive that lets downstream contracts and
agents gate actions on a consensus-verified public API operation. Revision
creators register immutable OpenAPI URL, base URL, operation path/method and
canonical query parameters. Attestations bind the live probe URL to that exact
operation, so a leader cannot substitute a different endpoint.

**Consensus:** Validators independently re-fetch the OpenAPI document and
execute the immutable bound probe. They derive operation identity, required
query parameters, probe path binding, HTTP result and JSON status themselves;
consensus requires exact equality of this whole record. `is_compatible` and
`is_continuously_compatible` are composable consumer gates.

**Limits:** Designed for public HTTPS GET/JSON interfaces. It proves a
point-in-time compatible response, not credentials, write-operation behavior,
or continuous availability.

**Live contract:** https://explorer-studio.genlayer.com/address/0xaD2639c2a9dD38C8B1Ed8dD9d6781545Aa8CF9F7

**Deployment transaction:** https://explorer-studio.genlayer.com/tx/0x226e14ef3d1a91c570f298e760d566558896b21ff5256cc7e5babda456a1a04d
