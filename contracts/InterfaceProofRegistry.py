# { "Depends": "py-genlayer:1jb45aa8ynh2a9c9xn3b7qqh8sm5q93hwfp7jqmwsfhh8jpz09h6" }

"""Consensus-verified OpenAPI operation compatibility attestations.

An API consumer registers an immutable interface revision: public OpenAPI URL,
operation path/method and its required query parameters.  On attestation, the
leader and every validator independently fetch the specification and execute the
bound public probe.  Only a canonical, fully recomputed compatibility record is
stored; the leader cannot choose its own result or decouple a probe from its
declared operation.
"""

from genlayer import *
import json
import re
from urllib.parse import urlencode, urlsplit

POLICY_VERSION = "interfaceproof-v1"
MAX_ID = 80
MAX_URL = 500
MAX_PATH = 180
MAX_QUERY = 800
ERR_EXPECTED = "[EXPECTED]"
ERR_EXTERNAL = "[EXTERNAL]"
ERR_TRANSIENT = "[TRANSIENT]"


def _id(value: str, label: str) -> str:
    value = str(value or "").strip().lower()
    if len(value) < 3 or len(value) > MAX_ID or re.fullmatch(r"[a-z0-9][a-z0-9._-]*", value) is None:
        raise gl.vm.UserError(f"{ERR_EXPECTED} invalid {label}")
    return value


def _public_https(url: str) -> bool:
    try:
        parsed = urlsplit(url)
        host = str(parsed.hostname or "").lower()
    except Exception:
        return False
    if parsed.scheme != "https" or not host or parsed.username or parsed.password:
        return False
    if host == "localhost" or host.endswith(".local") or host.endswith(".internal"):
        return False
    private = (r"127(?:\.[0-9]{1,3}){3}", r"10(?:\.[0-9]{1,3}){3}",
               r"192\.168(?:\.[0-9]{1,3}){2}", r"169\.254(?:\.[0-9]{1,3}){2}")
    if any(re.fullmatch(pattern, host) for pattern in private):
        return False
    match = re.fullmatch(r"172\.([0-9]{1,2})(?:\.[0-9]{1,3}){2}", host)
    return match is None or not (16 <= int(match.group(1)) <= 31)


def _json_response(url: str):
    try:
        response = gl.nondet.web.get(url, headers={"Accept": "application/json", "User-Agent": "InterfaceProof/1"})
    except Exception:
        raise gl.vm.UserError(f"{ERR_TRANSIENT} request failed")
    status = int(getattr(response, "status", 0) or 0)
    if 400 <= status < 500:
        raise gl.vm.UserError(f"{ERR_EXTERNAL} HTTP {status}")
    if status == 0 or status >= 500:
        raise gl.vm.UserError(f"{ERR_TRANSIENT} endpoint unavailable")
    body = getattr(response, "body", b"")
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="ignore")
    try:
        return status, json.loads(str(body))
    except Exception:
        raise gl.vm.UserError(f"{ERR_EXTERNAL} invalid JSON response")


def _canonical_query(raw: str) -> dict:
    try:
        value = json.loads(raw)
    except Exception:
        raise gl.vm.UserError(f"{ERR_EXPECTED} invalid query JSON")
    if not isinstance(value, dict) or not value:
        raise gl.vm.UserError(f"{ERR_EXPECTED} query must be a non-empty object")
    result = {}
    for key, item in value.items():
        key, item = str(key).strip(), str(item).strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", key) or not item or len(item) > 160:
            raise gl.vm.UserError(f"{ERR_EXPECTED} invalid query parameter")
        result[key] = item
    return dict(sorted(result.items()))


def _operation(spec: dict) -> dict:
    """Canonical evidence derived from the spec itself, not leader-provided text."""
    _, document = _json_response(spec["openapi_url"])
    paths = document.get("paths", {}) if isinstance(document, dict) else {}
    path_item = paths.get(spec["operation_path"]) if isinstance(paths, dict) else None
    op = path_item.get(spec["method"]) if isinstance(path_item, dict) else None
    if not isinstance(op, dict):
        return {"operation_present": False, "required_query_parameters": [], "operation_id": ""}
    required = []
    inherited = path_item.get("parameters", []) if isinstance(path_item.get("parameters", []), list) else []
    own = op.get("parameters", []) if isinstance(op.get("parameters", []), list) else []
    for parameter in inherited + own:
        if isinstance(parameter, dict) and parameter.get("in") == "query" and parameter.get("required") is True:
            name = str(parameter.get("name", "")).strip()
            if name:
                required.append(name)
    return {"operation_present": True, "required_query_parameters": sorted(set(required)),
            "operation_id": str(op.get("operationId", ""))[:120]}


def _recompute(spec: dict) -> dict:
    operation = _operation(spec)
    declared = sorted(spec["query"].keys())
    required = operation["required_query_parameters"]
    query_complete = all(name in spec["query"] for name in required)
    # Operation-path binding: this URL is always constructed from the immutable
    # base URL, exact operation path, and canonical registered query parameters.
    probe_url = spec["base_url"].rstrip("/") + spec["operation_path"] + "?" + urlencode(spec["query"])
    probe_status, probe_json = _json_response(probe_url)
    probe_matches_operation_path = urlsplit(probe_url).path == spec["operation_path"]
    response_json = isinstance(probe_json, (dict, list))
    compatible = bool(operation["operation_present"] and query_complete and probe_matches_operation_path
                      and 200 <= probe_status < 300 and response_json)
    return {
        "compatible": compatible,
        "operation_present": operation["operation_present"],
        "operation_id": operation["operation_id"],
        "required_query_parameters": required,
        "declared_query_parameters": declared,
        "query_parameters_complete": query_complete,
        "probe_matches_operation_path": probe_matches_operation_path,
        "probe_status": probe_status,
        "response_is_json": response_json,
        "probe_url": probe_url,
    }


def _same_public(left: dict, right: dict) -> bool:
    return json.dumps(left, sort_keys=True, separators=(",", ":")) == json.dumps(right, sort_keys=True, separators=(",", ":"))


class InterfaceProofRegistry(gl.Contract):
    revision_json: TreeMap[str, str]
    attestation_json: TreeMap[str, str]
    latest_by_revision: TreeMap[str, str]
    revision_creator: TreeMap[str, Address]
    revision_ids: DynArray[str]
    attestation_ids: DynArray[str]
    revision_count: u256
    attestation_count: u256

    def __init__(self) -> None:
        self.revision_count = u256(0)
        self.attestation_count = u256(0)

    @gl.public.write
    def register_revision(self, revision_id: str, name: str, openapi_url: str, base_url: str,
                          operation_path: str, method: str, query_json: str) -> dict:
        revision_id = _id(revision_id, "revision id")
        if self.revision_json.get(revision_id, ""):
            raise gl.vm.UserError(f"{ERR_EXPECTED} revision already exists")
        openapi_url, base_url = str(openapi_url).strip(), str(base_url).strip().rstrip("/")
        operation_path, method = str(operation_path).strip(), str(method).strip().lower()
        if not _public_https(openapi_url) or not _public_https(base_url):
            raise gl.vm.UserError(f"{ERR_EXPECTED} URLs must be public HTTPS")
        if len(operation_path) < 2 or len(operation_path) > MAX_PATH or not operation_path.startswith("/") or "?" in operation_path:
            raise gl.vm.UserError(f"{ERR_EXPECTED} invalid operation path")
        if method != "get":
            raise gl.vm.UserError(f"{ERR_EXPECTED} only GET operations are supported")
        if len(query_json) > MAX_QUERY:
            raise gl.vm.UserError(f"{ERR_EXPECTED} query too long")
        spec = {"revision_id": revision_id, "name": str(name).strip()[:120], "openapi_url": openapi_url,
                "base_url": base_url, "operation_path": operation_path, "method": method,
                "query": _canonical_query(query_json), "creator": str(gl.message.sender_address),
                "policy_version": POLICY_VERSION}
        if not spec["name"]:
            raise gl.vm.UserError(f"{ERR_EXPECTED} name required")
        self.revision_json[revision_id] = json.dumps(spec, sort_keys=True)
        self.revision_creator[revision_id] = gl.message.sender_address
        self.revision_ids.append(revision_id)
        self.revision_count = u256(int(self.revision_count) + 1)
        return spec

    def _attest(self, spec: dict) -> dict:
        def leader_fn():
            return {"public": _recompute(spec)}

        def validator_fn(leader_result) -> bool:
            if not isinstance(leader_result, gl.vm.Return) or not isinstance(leader_result.calldata, dict):
                return False
            claimed = leader_result.calldata.get("public")
            if not isinstance(claimed, dict):
                return False
            try:
                return _same_public(claimed, _recompute(spec))
            except Exception:
                return False

        result = gl.vm.run_nondet_unsafe(leader_fn, validator_fn)
        try:
            public = result.get("public")
            locally_recomputed = _recompute(spec)
            if not isinstance(public, dict) or not _same_public(public, locally_recomputed):
                raise gl.vm.UserError(f"{ERR_EXTERNAL} leader record is not bound to canonical recomputation")
            return public
        except gl.vm.UserError:
            raise
        except Exception:
            raise gl.vm.UserError(f"{ERR_TRANSIENT} invalid consensus result")

    @gl.public.write
    def attest_interface(self, revision_id: str, attestation_id: str) -> dict:
        revision_id, attestation_id = _id(revision_id, "revision id"), _id(attestation_id, "attestation id")
        if self.attestation_json.get(attestation_id, ""):
            raise gl.vm.UserError(f"{ERR_EXPECTED} attestation already exists")
        encoded = self.revision_json.get(revision_id, "")
        if not encoded:
            raise gl.vm.UserError(f"{ERR_EXPECTED} revision not found")
        spec, public = json.loads(encoded), self._attest(json.loads(encoded))
        record = {"attestation_id": attestation_id, "revision_id": revision_id, "verified": True,
                  "verification_mode": "exact-recomputed-interface-record", "policy_version": POLICY_VERSION,
                  "attester": str(gl.message.sender_address), **public}
        self.attestation_json[attestation_id] = json.dumps(record, sort_keys=True)
        self.latest_by_revision[revision_id] = attestation_id
        self.attestation_ids.append(attestation_id)
        self.attestation_count = u256(int(self.attestation_count) + 1)
        return record

    @gl.public.view
    def get_revision(self, revision_id: str) -> dict:
        encoded = self.revision_json.get(_id(revision_id, "revision id"), "")
        if not encoded:
            raise gl.vm.UserError(f"{ERR_EXPECTED} revision not found")
        return json.loads(encoded)

    @gl.public.view
    def get_attestation(self, attestation_id: str) -> dict:
        encoded = self.attestation_json.get(_id(attestation_id, "attestation id"), "")
        if not encoded:
            raise gl.vm.UserError(f"{ERR_EXPECTED} attestation not found")
        return json.loads(encoded)

    @gl.public.view
    def is_compatible(self, attestation_id: str) -> bool:
        record = self.get_attestation(attestation_id)
        return bool(record.get("verified") is True and record.get("compatible") is True
                    and record.get("probe_matches_operation_path") is True
                    and record.get("query_parameters_complete") is True)

    @gl.public.view
    def is_continuously_compatible(self, revision_id: str) -> bool:
        """Consumer gate for the most recently finalized immutable attestation."""
        revision_id = _id(revision_id, "revision id")
        latest = self.latest_by_revision.get(revision_id, "")
        return bool(latest) and self.is_compatible(latest)

    @gl.public.view
    def get_latest(self, revision_id: str) -> dict:
        latest = self.latest_by_revision.get(_id(revision_id, "revision id"), "")
        if not latest:
            raise gl.vm.UserError(f"{ERR_EXPECTED} revision has no attestation")
        return self.get_attestation(latest)

    @gl.public.view
    def get_model_card(self) -> dict:
        return {"name": "InterfaceProof Registry", "policy_version": POLICY_VERSION,
                "purpose": "Reusable consensus primitive for verifying public OpenAPI operation compatibility.",
                "consensus": "Validators independently fetch the specification and bound live operation, then require exact equality of the recomputed public record.",
                "consumer_gates": ["is_compatible", "is_continuously_compatible"]}
