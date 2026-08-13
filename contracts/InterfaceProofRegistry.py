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

POLICY_VERSION = "interfaceproof-v4-negative-freshness"
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


def _probe_response(url: str) -> dict:
    """Total probe outcome: endpoint failures become consensus-stored negatives."""
    try:
        response = gl.nondet.web.get(url, headers={"Accept": "application/json", "User-Agent": "InterfaceProof/1"})
    except Exception:
        return {"probe_status": 0, "probe_outcome": "REQUEST_FAILED", "response_is_json": False}
    status = int(getattr(response, "status", 0) or 0)
    body = getattr(response, "body", b"")
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="ignore")
    if 400 <= status < 500:
        return {"probe_status": status, "probe_outcome": "HTTP_4XX", "response_is_json": False}
    if status == 0 or status >= 500:
        return {"probe_status": status, "probe_outcome": "HTTP_5XX", "response_is_json": False}
    try:
        parsed = json.loads(str(body))
        is_json = isinstance(parsed, (dict, list))
    except Exception:
        is_json = False
    return {"probe_status": status, "probe_outcome": "OK_JSON" if is_json else "INVALID_JSON",
            "response_is_json": is_json}


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


def _normalized_server(url: str) -> str:
    """Canonical form for an absolute, query-free HTTPS OpenAPI server."""
    try:
        parsed = urlsplit(str(url).strip())
    except Exception:
        return ""
    if (parsed.scheme != "https" or not parsed.netloc or parsed.query or parsed.fragment
            or parsed.username or parsed.password):
        return ""
    return f"https://{parsed.netloc.lower()}{parsed.path.rstrip('/')}"


def _declared_servers(document: dict, openapi_url: str) -> list:
    servers = document.get("servers", []) if isinstance(document, dict) else []
    result = []
    for item in servers if isinstance(servers, list) else []:
        if isinstance(item, dict):
            raw = str(item.get("url", "")).strip()
            # OpenAPI permits relative server URLs. Resolve them only against
            # the immutable HTTPS specification URL; templates stay unsupported.
            if raw.startswith("/"):
                parsed_document = urlsplit(openapi_url)
                raw = f"{parsed_document.scheme}://{parsed_document.netloc}{raw}"
            server = _normalized_server(raw) if "{" not in raw else ""
            if server:
                result.append(server)
    return sorted(set(result))


def _operation(spec: dict) -> dict:
    """Canonical evidence derived from the spec itself, not leader-provided text."""
    _, document = _json_response(spec["openapi_url"])
    declared_servers = _declared_servers(document, spec["openapi_url"])
    base_server_declared = _normalized_server(spec["base_url"]) in declared_servers
    paths = document.get("paths", {}) if isinstance(document, dict) else {}
    path_item = paths.get(spec["operation_path"]) if isinstance(paths, dict) else None
    op = path_item.get(spec["method"]) if isinstance(path_item, dict) else None
    if not isinstance(op, dict):
        return {"operation_present": False, "required_query_parameters": [], "operation_id": "",
                "declared_servers": declared_servers, "base_server_declared": base_server_declared}
    required = []
    inherited = path_item.get("parameters", []) if isinstance(path_item.get("parameters", []), list) else []
    own = op.get("parameters", []) if isinstance(op.get("parameters", []), list) else []
    for parameter in inherited + own:
        if isinstance(parameter, dict) and parameter.get("in") == "query" and parameter.get("required") is True:
            name = str(parameter.get("name", "")).strip()
            if name:
                required.append(name)
    return {"operation_present": True, "required_query_parameters": sorted(set(required)),
            "operation_id": str(op.get("operationId", ""))[:120],
            "declared_servers": declared_servers, "base_server_declared": base_server_declared}


def _recompute(spec: dict) -> dict:
    operation = _operation(spec)
    declared = sorted(spec["query"].keys())
    required = operation["required_query_parameters"]
    query_complete = all(name in spec["query"] for name in required)
    # Operation-path binding: this URL is always constructed from the immutable
    # base URL, exact operation path, and canonical registered query parameters.
    probe_url = spec["base_url"].rstrip("/") + spec["operation_path"] + "?" + urlencode(spec["query"])
    probe = _probe_response(probe_url)
    probe_status = probe["probe_status"]
    expected_probe_path = urlsplit(spec["base_url"]).path.rstrip("/") + spec["operation_path"]
    probe_matches_operation_path = urlsplit(probe_url).path == expected_probe_path
    response_json = probe["response_is_json"]
    compatible = bool(operation["operation_present"] and operation["base_server_declared"] and query_complete and probe_matches_operation_path
                      and probe["probe_outcome"] == "OK_JSON" and 200 <= probe_status < 300 and response_json)
    return {
        "compatible": compatible,
        "operation_present": operation["operation_present"],
        "operation_id": operation["operation_id"],
        "declared_servers": operation["declared_servers"],
        "base_server_declared": operation["base_server_declared"],
        "required_query_parameters": required,
        "declared_query_parameters": declared,
        "query_parameters_complete": query_complete,
        "probe_matches_operation_path": probe_matches_operation_path,
        "probe_status": probe_status,
        "probe_outcome": probe["probe_outcome"],
        "response_is_json": response_json,
        "probe_url": probe_url,
    }


def _same_public(left: dict, right: dict) -> bool:
    return json.dumps(left, sort_keys=True, separators=(",", ":")) == json.dumps(right, sort_keys=True, separators=(",", ":"))


def _validate_public_record(public: dict, spec: dict) -> dict:
    """Validate consensus output without performing a second web fetch.

    The substantive record has already been independently recomputed by every
    validator. This deterministic pass binds all stored fields to each other and
    to the immutable revision before state is written.
    """
    expected_keys = sorted([
        "compatible", "operation_present", "operation_id", "declared_servers",
        "base_server_declared", "required_query_parameters", "declared_query_parameters",
        "query_parameters_complete", "probe_matches_operation_path", "probe_status",
        "response_is_json", "probe_outcome", "probe_url",
    ])
    if not isinstance(public, dict) or sorted(public.keys()) != expected_keys:
        raise gl.vm.UserError(f"{ERR_EXTERNAL} consensus returned an invalid public record")
    boolean_fields = ["compatible", "operation_present", "base_server_declared",
                      "query_parameters_complete", "probe_matches_operation_path", "response_is_json"]
    if any(not isinstance(public.get(field), bool) for field in boolean_fields):
        raise gl.vm.UserError(f"{ERR_EXTERNAL} consensus returned invalid boolean fields")
    if not isinstance(public.get("probe_status"), int) or isinstance(public.get("probe_status"), bool):
        raise gl.vm.UserError(f"{ERR_EXTERNAL} consensus returned invalid probe status")
    if public.get("probe_outcome") not in ["OK_JSON", "HTTP_4XX", "HTTP_5XX", "REQUEST_FAILED", "INVALID_JSON"]:
        raise gl.vm.UserError(f"{ERR_EXTERNAL} consensus returned invalid probe outcome")
    if not isinstance(public.get("operation_id"), str):
        raise gl.vm.UserError(f"{ERR_EXTERNAL} consensus returned invalid operation id")
    declared_servers = public.get("declared_servers")
    required = public.get("required_query_parameters")
    declared = public.get("declared_query_parameters")
    if not isinstance(declared_servers, list) or not isinstance(required, list) or not isinstance(declared, list):
        raise gl.vm.UserError(f"{ERR_EXTERNAL} consensus returned invalid list fields")
    if declared_servers != sorted(set([str(item) for item in declared_servers])):
        raise gl.vm.UserError(f"{ERR_EXTERNAL} declared servers are not canonical")
    if required != sorted(set([str(item) for item in required])):
        raise gl.vm.UserError(f"{ERR_EXTERNAL} required parameters are not canonical")
    expected_declared = sorted(spec["query"].keys())
    if declared != expected_declared:
        raise gl.vm.UserError(f"{ERR_EXTERNAL} declared parameters do not match revision")
    expected_probe = spec["base_url"].rstrip("/") + spec["operation_path"] + "?" + urlencode(spec["query"])
    if public.get("probe_url") != expected_probe:
        raise gl.vm.UserError(f"{ERR_EXTERNAL} probe URL does not match revision")
    expected_probe_path = urlsplit(spec["base_url"]).path.rstrip("/") + spec["operation_path"]
    path_bound = urlsplit(expected_probe).path == expected_probe_path
    server_bound = _normalized_server(spec["base_url"]) in declared_servers
    query_complete = all(name in spec["query"] for name in required)
    if public["probe_matches_operation_path"] != path_bound:
        raise gl.vm.UserError(f"{ERR_EXTERNAL} probe path flag is inconsistent")
    if public["base_server_declared"] != server_bound:
        raise gl.vm.UserError(f"{ERR_EXTERNAL} server binding flag is inconsistent")
    if public["query_parameters_complete"] != query_complete:
        raise gl.vm.UserError(f"{ERR_EXTERNAL} query completeness flag is inconsistent")
    expected_compatible = bool(public["operation_present"] and server_bound and query_complete and path_bound
                               and public["probe_outcome"] == "OK_JSON"
                               and 200 <= public["probe_status"] < 300 and public["response_is_json"])
    if public["compatible"] != expected_compatible:
        raise gl.vm.UserError(f"{ERR_EXTERNAL} compatibility flag is inconsistent")
    return public


class InterfaceProofRegistry(gl.Contract):
    revision_json: TreeMap[str, str]
    attestation_json: TreeMap[str, str]
    latest_by_revision: TreeMap[str, str]
    latest_sequence_by_revision: TreeMap[str, u256]
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
        openapi_url, base_url = str(openapi_url).strip(), _normalized_server(base_url)
        operation_path, method = str(operation_path).strip(), str(method).strip().lower()
        if not _public_https(openapi_url) or not base_url or not _public_https(base_url):
            raise gl.vm.UserError(f"{ERR_EXPECTED} URLs must be public HTTPS without query or fragment")
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
            return _validate_public_record(public, spec)
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
        sequence = int(self.attestation_count) + 1
        record = {"attestation_id": attestation_id, "revision_id": revision_id, "verified": True,
                  "attestation_sequence": sequence,
                  "verification_mode": "exact-recomputed-interface-record", "policy_version": POLICY_VERSION,
                  "attester": str(gl.message.sender_address), **public}
        self.attestation_json[attestation_id] = json.dumps(record, sort_keys=True)
        self.latest_by_revision[revision_id] = attestation_id
        self.latest_sequence_by_revision[revision_id] = u256(sequence)
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
                    and record.get("base_server_declared") is True
                    and record.get("probe_matches_operation_path") is True
                    and record.get("query_parameters_complete") is True)

    @gl.public.view
    def is_continuously_compatible(self, revision_id: str) -> bool:
        """Strict latest-result gate; any stored negative immediately closes it."""
        revision_id = _id(revision_id, "revision id")
        latest = self.latest_by_revision.get(revision_id, "")
        return bool(latest) and self.is_compatible(latest)

    @gl.public.view
    def is_fresh_and_compatible(self, revision_id: str, max_age_attestations: u256) -> bool:
        """Compatibility plus explicit logical freshness against registry sequence."""
        revision_id = _id(revision_id, "revision id")
        latest = self.latest_by_revision.get(revision_id, "")
        if not latest:
            return False
        latest_sequence = int(self.latest_sequence_by_revision.get(revision_id, u256(0)))
        age = int(self.attestation_count) - latest_sequence
        return age <= int(max_age_attestations) and self.is_compatible(latest)

    @gl.public.view
    def get_freshness(self, revision_id: str) -> dict:
        revision_id = _id(revision_id, "revision id")
        latest = self.latest_by_revision.get(revision_id, "")
        latest_sequence = int(self.latest_sequence_by_revision.get(revision_id, u256(0)))
        return {"has_attestation": bool(latest), "latest_attestation_id": latest,
                "latest_sequence": latest_sequence, "current_sequence": int(self.attestation_count),
                "age_attestations": int(self.attestation_count) - latest_sequence if latest else 0}

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
                "freshness_unit": "finalized registry attestations since this revision's latest result",
                "consumer_gates": ["is_compatible", "is_continuously_compatible", "is_fresh_and_compatible"]}
