# RAE-CRL 2.2 and RAE-Mesh
## Cognitive Research Layer and Federated Memory Architecture, Security, Isolation, Supply-Chain, and Delivery Plan

**Status:** Revised Reference Plan  
**Revision:** 2.2  
**Scope:** RAE-CRL, RAE-Mesh, RAE-Core, RAE-Lab, Phoenix, Hive, Quality Tribunal, A2A Bridge  
**Target environments:** Academic laboratories, R&D departments, regulated organizations, and multi-team federations  
**Priorities:** Epistemic integrity, reproducibility, auditability, IP control, workload isolation, resilience, model-agnostic interoperability, verifiable software supply chain, continuous vulnerability management, and ISO/IEC 27001 control alignment  
**Design ethos:** One explicit identity model. One canonical encoding. One hash suite per federation profile. One typed edge grammar. Append-only history. Default-deny execution. Verify signatures at every trust boundary, not once. Security posture is a lifecycle, not an admission event.

---

## 1. Purpose and boundaries

RAE-CRL is the Cognitive Research Layer of RAE-Suite. It provides:

1. Explicit registration of authored or imported epistemic artifacts.
2. A typed provenance DAG connecting hypotheses, assumptions, experiments, observations, decisions, reviews, and evidence.
3. An append-only Epistemic Event Journal for every accepted transition.
4. Automated detection of bounded logical conflict candidates.
5. Preservation of negative knowledge without silent deletion or history rewriting.
6. Reproducible experiment execution through Hive isolation profiles.
7. Controlled artifact exchange through RAE-Mesh and Consensual Memory Transfer.
8. Signed, timestamped, independently verifiable Evidence Packages carrying SBOM and VEX evidence.
9. Auditable APIs and federation protocols.
10. Resource governance that prevents experiments or graph queries from exhausting a node.
11. A continuously operated application-security and vulnerability-management program covering the platform, experiment images, and published artifacts.

### 1.1 Non-goals

RAE-CRL does not:

- replace researchers, reviewers, ethics boards, or accountable decision-makers;
- expose private chain-of-thought or require hidden reasoning;
- infer and register epistemic artifacts without explicit provenance and policy;
- declare a hypothesis true solely from model output;
- treat a Docker container or Kubernetes pod as a complete security boundary;
- promise recall of plaintext already disclosed to a federation peer;
- claim ISO/IEC 27001 certification by architecture alone;
- claim that an SBOM or a clean scan at seal time guarantees absence of vulnerabilities at reproduction time; VEX and advisory linkage exist precisely because this claim would be false.

### 1.2 Non-negotiable rules

- Every accepted state transition and security-sensitive denial emits an event.
- No sealed version is mutated.
- No unclassified artifact is admitted.
- No experiment receives network access unless its execution grant explicitly allows it.
- No experiment receives host namespaces, runtime sockets, unrestricted devices, or privileged mode.
- No absolute project filesystem references are stored or accepted.
- No model-generated conflict reaches `CONFIRMED` without authorized review.
- No federation silently changes canonical encoding or hash algorithms.
- No image, dependency set, or platform component executes without a verifiable signature and SBOM under the deployment trust policy.
- No publication package ships without SBOM references and a security-posture declaration for its execution closure.
- No admitted image is exempt from continuous rescanning while referenced by an active project.

---

## 2. Constitutional alignment

| Suite principle | RAE-CRL implementation |
|---|---|
| Memory-First | Artifacts and events are first-class memory records. Journal events map to sensory and episodic memory; active artifacts to working and semantic memory; sealed versions to long-term memory; conflict and review outputs to reflective memory. |
| C6: project-relative only | Stored file references use project-relative URIs. Absolute paths, traversal segments, ambiguous separators, and host path mounts are rejected — at Tribunal seal time and as left-shifted SAST rules in CI. |
| Modular Roles | Phoenix plans and repairs workflows; Hive executes isolated workloads; Quality Tribunal validates transitions and releases; Lab performs bounded Kaizen optimization; RAE-Core owns identity, journal, and policy enforcement. |
| Auto-Enforcement | Admission, AST, graph, information-flow, dependency, image-signature, SBOM, vulnerability, and sandbox-policy gates fail closed. Tribunal AST rules are mirrored into CI SAST so violations are caught pre-merge, not only pre-seal. |
| Sandbox Isolation | Experiments run in ephemeral source workspaces and isolated OCI or microVM environments under explicit resource and network policies. |
| A2A Bridge | Inter-role messages are authenticated, authorized, schema-validated, correlated, and journaled. |
| MAB and Kaizen | Tuning occurs only inside declared bounds and cannot alter constitutional gates, classification policy, reviewer requirements, or supply-chain verification policy. |
| RAE-Mesh and CMT | Transfer requires peer trust, explicit scope, recipient consent, policy compatibility, cryptographic receipts, and content-safety scanning of received payloads. |

---

## 3. Canonical data and identity model

### 3.1 Identifiers

| Identifier | Type | Meaning |
|---|---|---|
| `artifact_id` | UUIDv7 | Stable logical artifact handle. Uniqueness is global; authorization remains tenant- and project-scoped. |
| `tenant_id` | ULID | Tenant isolation domain. |
| `project_id` | ULID | Project boundary. |
| `event_id` | UUIDv7 | Journal event identity. |
| `execution_id` | UUIDv7 | Hive execution attempt identity. |
| `transfer_id` | UUIDv7 | CMT transaction identity. |
| `version_cid` | Multihash | Immutable sealed-version identity. |
| `advisory_id` | Namespaced string | Security advisory identity (internal ID plus CVE where assigned). |
| `principal` | Issuer plus subject | OIDC identity represented by both `iss` and `sub`; neither is trusted alone. |

Database uniqueness and authorization use at least:

`tenant_id + project_id + artifact_id`

A UUID value is never treated as proof of tenancy or authority.

### 3.2 Canonical encoding

The canonical wire and hash encoding is deterministic CBOR conforming to RFC 8949 deterministic encoding requirements.

Canonicalization rules include:

- map keys sorted according to deterministic CBOR;
- timestamps normalized to UTC RFC 3339 with defined fractional precision;
- Unicode normalized to NFC where text semantics permit;
- units represented using declared unit identifiers;
- no floating-point NaN or infinity unless a schema explicitly defines them;
- decimal measurements encoded as exact decimal structures when precision matters;
- sets sorted by canonical encoded byte order;
- duplicate map keys rejected;
- unknown critical fields rejected;
- schema version included in the hashed record.

JSON may be offered as an API representation, but JSON is not hashed directly.

The canonical CBOR codec is a critical trust component: it receives continuous coverage-guided fuzzing, differential testing across independent implementations, and memory-safety requirements per Section 14.

### 3.3 Hash profiles

The default federation profile uses BLAKE3-256.

A regulated deployment may define a separate approved profile, such as SHA-256, when required by its cryptographic policy. The following rules apply:

1. The algorithm identifier is encoded in every multihash.
2. Hash selection is explicit in federation metadata.
3. A node never silently substitutes one algorithm for another.
4. Peers with incompatible mandatory profiles do not merge identities.
5. Cross-profile exports may carry both source and target manifests, but the resulting CIDs are distinct.
6. Signatures bind the profile identifier and version CID.

“One canonical hash” means one mandatory hash suite within a federation profile, not hidden compile-time substitution.

### 3.4 Sealed version record

A sealed version is:

`version_cid = hash(canonical_cbor(version_record))`

The hashed `version_record` contains:

| Field | Description |
|---|---|
| `artifact_id` | Logical artifact identity |
| `tenant_id` | Tenant domain |
| `project_id` | Project scope |
| `artifact_type` | Closed type identifier |
| `schema_version` | Artifact schema version |
| `prev_version_cid` | Previous sealed version or null |
| `classification` | Label and compartments |
| `author_principal` | OIDC issuer and subject |
| `authorship_kind` | Human, imported, automated, or jointly authored |
| `created_at` | Creation timestamp |
| `edges` | Canonically ordered typed edges |
| `payload` | Type-specific canonical payload |
| `retention` | Retention policy reference and trigger |
| `policy_tags` | Canonically ordered policy labels |
| `generation_context` | Model, tool, or importer metadata when applicable |

Including `prev_version_cid` in the hashed record makes the version chain tamper-evident.

### 3.5 Drafts, versions, and projections

- Draft state may change, but each accepted draft operation emits a journal event.
- A draft has no authoritative `version_cid`.
- Sealing creates a new immutable version.
- Lifecycle, consent, review, revocation, and legal-hold changes are represented as events.
- Current state is a rebuildable projection over sealed versions and events.
- Projections are disposable and are never the sole audit source.
- Event insertion and state transition are committed atomically.

---

## 4. Artifact model

### 4.1 Closed artifact types

| Type | Purpose |
|---|---|
| `Hypothesis` | Falsifiable claim with variables, scope, and test predicate |
| `Assumption` | Scope-bounded presupposition |
| `Experiment` | Protocol, execution specification, and execution references |
| `Observation` | Measurement with instrument, unit, uncertainty, and context |
| `Decision` | Conclusion with justification and authority |
| `Evidence` | Cryptographic or evidentiary proof object |
| `ConflictCandidate` | Potential inconsistency requiring disposition |
| `Review` | Human or automated assessment |
| `Trace` | Signed checkpoint or exportable segment of journal history |
| `PublicationPackage` | Sealed export manifest and dependency closure |
| `SecurityAdvisory` | Signed post-seal vulnerability or revocation notice linked to affected version CIDs |

Adding an artifact type requires a schema-major governance decision.

`SecurityAdvisory` artifacts allow already sealed evidence to remain immutable while making later-discovered vulnerabilities, key compromises, or content-safety findings discoverable and machine-linkable.

### 4.2 Prohibited content

The following is rejected:

- implicit or private chain-of-thought;
- fabricated citations or sources;
- artifacts with no classification;
- artifacts with unresolved absolute paths;
- opaque executable payloads outside an `Experiment`;
- unsafe serialization formats (e.g., raw pickle) presented as data artifacts, unless admitted under a reviewed deserialization exception per Section 16;
- mutable external references presented as immutable evidence;
- secrets embedded in artifact payloads;
- unsigned imports when policy requires authenticated origin;
- content failing malicious-content scanning per Section 16, pending quarantine review.

Models may provide concise rationales, citations, structured variables, confidence, and tool results. They must not be required to expose private hidden reasoning.

---

## 5. Typed provenance edge grammar

### 5.1 Edge structure

Each edge contains:

| Field | Description |
|---|---|
| `edge_type` | Controlled relation |
| `target_artifact_id` | Logical target |
| `target_version_cid` | Required for sealed evidentiary references |
| `scope` | Optional variable, temporal, spatial, or dataset scope |
| `asserted_by` | Principal or system role |
| `asserted_at` | Timestamp |
| `classification_effect` | Inherit, constrain, sanitize, or none |
| `metadata` | Schema-bounded relation metadata |

### 5.2 Edge vocabulary

The baseline vocabulary is:

- `DERIVED_FROM`
- `SUPPORTED_BY`
- `REFUTED_BY`
- `ASSUMES`
- `TESTED_BY`
- `PRODUCED`
- `OBSERVED_IN`
- `JUSTIFIES`
- `REVIEWS`
- `REPLICATES`
- `CONTRADICTS`
- `SUPERSEDES`
- `IMPORTS`
- `EXECUTED_AS`
- `SEALED_IN`
- `SANITIZED_FROM`
- `AFFECTED_BY` (sealed version → `SecurityAdvisory`)

Unknown edge types are rejected unless introduced by an approved schema extension.

### 5.3 Graph constraints

- Self-edges are rejected unless specifically allowed for a checkpoint relation.
- Provenance relations declared acyclic are cycle-checked at admission.
- Version history is a single-parent chain unless an explicit merge artifact is created.
- A merge records all source versions through typed edges and one previous local version.
- Sealed evidentiary edges must target a `version_cid`, not merely a logical artifact.
- Graph traversal has explicit depth, node-count, time, and memory bounds.
- Cross-tenant edges require an accepted CMT receipt or an approved external reference.
- `AFFECTED_BY` edges may be added to the graph after sealing; they do not mutate the sealed version record and are journaled like any other event.

---

## 6. Epistemic Event Journal and Trace checkpoints

### 6.1 Event journal

The journal is append-only and records:

- draft creation and update;
- seal requests and outcomes;
- lifecycle transitions;
- reviews and Tribunal decisions;
- classification changes;
- legal holds and disposition;
- execution grants and denials;
- Hive execution state;
- CMT offers, acceptance, delivery, receipt, revocation, and deletion attestations;
- policy and key changes;
- security-sensitive denials;
- vulnerability rescan findings, advisory publication, and VEX status changes affecting admitted images or sealed evidence;
- administrative actions.

Each event includes:

- `event_id`;
- tenant, project, and correlation identifiers;
- actor and delegated actor;
- event type and schema version;
- timestamp and monotonic sequence within the journal partition;
- affected artifact, version, execution, or transfer;
- previous event-chain hash;
- event payload;
- policy decision identifier;
- authenticated source;
- event hash and optional signature.

### 6.2 Atomicity

The command result, artifact transition, and journal event are committed in one transaction or through a transactional outbox with equivalent durability guarantees.

An operation is not reported as successful until its audit event is durable.

### 6.3 Trace artifacts

A `Trace` artifact is a signed checkpoint over a bounded journal range. It contains:

- journal partition identifier;
- first and last event sequence;
- Merkle or chained-hash root;
- included event-type summary;
- signer;
- timestamp evidence;
- previous checkpoint reference.

Creating a checkpoint is recorded in the next journal range, preventing recursive checkpoint creation.

---

## 7. Lifecycle and preservation

### 7.1 Artifact lifecycle

Baseline lifecycle:

`DRAFT → SUBMITTED → REVIEWED → SEALED → SUPERSEDED`

Additional terminal or restrictive states:

- `REJECTED`
- `WITHDRAWN`
- `QUARANTINED`
- `REVOKED_FOR_USE`
- `TOMBSTONED`

Transitions are policy-controlled and event-sourced.

### 7.2 Conflict lifecycle

`PROPOSED → TRIAGED → UNDER_REVIEW → CONFIRMED | DISMISSED | DUPLICATE | OUT_OF_SCOPE`

Only authorized human reviewers or a configured Tribunal quorum may assign `CONFIRMED`.

### 7.3 Negative knowledge

Refuted hypotheses, failed experiments, null results, and dismissed conflict candidates remain discoverable according to authorization and retention policy.

They may not be silently overwritten or removed from history.

### 7.4 Retention and lawful deletion

Retention is represented by:

- policy identifier;
- trigger event;
- duration or explicit expiry;
- legal-hold status;
- disposition action;
- approving authority.

When deletion is legally required:

1. Access is suspended.
2. A disposition event is authorized and journaled.
3. Payload encryption keys may be destroyed.
4. Replicas receive the disposition request.
5. A tombstone retains the minimum legally permitted metadata, hash, reason, and authority.
6. Evidence packages record that content is unavailable and why.

“Immutable” means no undetectable rewriting; it does not override law.

---

## 8. Classification and information-flow control

### 8.1 Label model

A label consists of:

- a hierarchy level;
- zero or more compartments;
- tenant and project constraints;
- handling caveats;
- export restrictions.

Example hierarchy:

`PUBLIC < INTERNAL < CONFIDENTIAL < RESTRICTED`

Deployments may define stricter labels.

### 8.2 Effective classification

Unless an authorized sanitization rule applies, a derived artifact receives the least upper bound of:

- its declared label;
- all dependency labels;
- execution input labels;
- model and dataset restrictions;
- applicable policy tags.

### 8.3 Declassification

Declassification requires:

- a named authority;
- a declared sanitization method;
- a review artifact;
- an explicit `SANITIZED_FROM` edge;
- a journal event;
- a validation that prohibited information is absent.

Automated summarization alone is not declassification.

### 8.4 Enforcement points

Classification is enforced at:

- API authorization;
- graph query planning;
- search indexing;
- embedding or feature generation;
- experiment input staging;
- logs and telemetry;
- evidence export;
- CMT negotiation;
- cache admission;
- backup and restore;
- vulnerability scan reporting (scan findings inherit the classification of scanned content where applicable).

Telemetry must not contain artifact payloads or secrets by default.

---

## 9. Watchdog logical-conflict detection

### 9.1 Contradiction operator

The Watchdog may propose a conflict only when both claims can be normalized into a comparison context:

`Conflict(A, B, C)`

Where context `C` includes:

- variable bindings;
- ontology and schema versions;
- temporal interval;
- spatial or population scope;
- units and conversion rules;
- quantifiers;
- confidence and uncertainty;
- classification compatibility;
- assumption set.

A candidate contradiction requires one or more of:

- predicates that cannot both hold in the same context;
- mutually exclusive categorical values;
- non-overlapping numeric intervals after uncertainty and unit normalization;
- incompatible decision constraints;
- a direct refutation edge with adequate scope.

### 9.2 Candidate record

A `ConflictCandidate` records:

- exact source version CIDs;
- normalized propositions;
- relevant context;
- contradiction rule identifier;
- score and calibrated confidence;
- missing information;
- model and tool versions;
- concise explanation;
- false-positive risk;
- proposed remediation.

### 9.3 Safety and quality

- No silent truth assertion is permitted.
- Model output remains advisory.
- Duplicate candidates are clustered.
- Per-project candidate rates are limited.
- Low-confidence candidates may be batched rather than alerted individually.
- Threshold changes are versioned and evaluated on fixed benchmark sets.
- Kaizen may tune ranking weights but cannot remove reviewer requirements.
- Drift, calibration, precision, recall, and reviewer reversal rates are monitored.

---

## 10. Quality Tribunal and admission gates

### 10.1 Gate order

1. Authentication and authorization
2. Schema validation
3. Canonical encoding validation
4. Project-relative reference validation
5. Secret and credential scanning
6. Malicious-content and unsafe-deserialization scanning
7. Classification and information-flow validation
8. Typed-edge and graph validation
9. Dependency and import policy
10. Source and license policy
11. Container image signature, SBOM, and vulnerability policy
12. Epistemic completeness checks
13. Signature and timestamp policy
14. Tribunal review where required
15. Seal and journal commit

### 10.2 Required gates

The baseline includes:

- `NoAbsolutePathGate`
- `NoTraversalReferenceGate`
- `ArtifactClassificationGate`
- `PrincipalBindingGate`
- `CanonicalEncodingGate`
- `EdgeGrammarGate`
- `DAGCycleGate`
- `VersionChainGate`
- `ClassificationFlowGate`
- `SecretMaterialGate`
- `MaliciousContentGate`
- `UnsafeDeserializationGate`
- `ProhibitedImportGate`
- `DependencyPinningGate`
- `ImageDigestGate`
- `ImageSignatureGate`
- `ImageAttestationGate` (SLSA provenance and SBOM attestation presence and validity)
- `SBOMCompletenessGate`
- `VulnerabilityPolicyGate` (severity thresholds with KEV/EPSS-aware exceptions per Section 15)
- `SandboxPolicyGate`
- `NetworkGrantGate`
- `ResourceLimitGate`
- `EvidenceClosureGate`

Prohibited imports, including disallowed embedding libraries, are detected through AST inspection, lockfile inspection, package metadata, and runtime import tracing where warranted. The same rule packs run as CI SAST checks (Section 14) so violations fail pre-merge, not only pre-seal.

### 10.3 Gate behavior

- Gates fail closed.
- Every denial has a stable reason code.
- Overrides require a named authority, expiry, scope, and journal event.
- Constitutional gates cannot be overridden through normal project administration.
- Vulnerability-policy exceptions require a documented VEX-style justification (not affected, mitigated, or accepted-with-expiry) per Section 15.
- Gate versions and policy digests are included in sealed execution provenance.

---

## 11. Hive experiment isolation architecture

### 11.1 Threat model

Experiment code may be:

- buggy;
- dependency-compromised;
- intentionally hostile;
- designed to consume unbounded resources;
- designed to exfiltrate inputs;
- capable of probing neighboring workloads or host services;
- delivered through poisoned data artifacts (notebooks, serialized models, crafted scientific file formats) rather than source code.

Standard containers reduce accidental interference but do not alone provide sufficient isolation for hostile code.

### 11.2 Isolation profiles

| Profile | Intended workload | Runtime |
|---|---|---|
| `STANDARD` | Trusted first-party code with reviewed dependencies | Rootless OCI container |
| `HARDENED` | Third-party or model-generated code | Sandboxed runtime such as gVisor |
| `STRICT` | Untrusted code or sensitive multi-tenant processing | Kata Containers or microVM |
| `OFFLINE_STRICT` | High-sensitivity reproducibility work | MicroVM with no network and encrypted ephemeral storage |

Policy selects the minimum profile. Users may request stronger isolation but not weaker isolation. Artifacts flagged by the `UnsafeDeserializationGate` under a reviewed exception execute at `HARDENED` or stronger.

### 11.3 Source workspace

Each execution receives:

- an ephemeral git worktree or immutable source snapshot;
- a clean repository state;
- a recorded commit and tree identifier;
- no host repository credentials;
- no inherited developer configuration;
- project-relative input references;
- a separate output staging area;
- destruction after collection or expiry.

Dirty working state must be captured as a sealed patch or rejected.

### 11.4 Linux namespace requirements

For OCI-based profiles, Hive uses dedicated:

- user namespace;
- mount namespace;
- PID namespace;
- network namespace;
- IPC namespace;
- UTS namespace;
- cgroup namespace;
- time namespace when supported and reproducibility policy requires it.

The following are prohibited:

- host PID, network, IPC, UTS, user, or cgroup namespaces;
- privileged mode;
- host device passthrough unless explicitly approved;
- container-runtime sockets;
- host filesystem bind mounts;
- arbitrary kernel module access;
- unconfined security profiles.

### 11.5 Process privileges

Every workload:

- runs as a non-root identity inside the workload;
- maps to an unprivileged host identity through user namespaces;
- drops all Linux capabilities by default;
- enables `no_new_privs`;
- uses a default-deny seccomp profile;
- uses AppArmor or SELinux confinement where available;
- has a restrictive umask;
- cannot create setuid or setgid executables;
- cannot gain privileges through file capabilities;
- cannot access kernel keyrings or host credentials;
- cannot invoke disallowed namespace creation or mount operations.

A narrowly required capability needs a reviewed policy exception and a stronger isolation profile.

### 11.6 Filesystem isolation

- The root filesystem is read-only.
- Writable areas are explicit, ephemeral, and quota-limited.
- Temporary storage uses bounded tmpfs or bounded ephemeral volumes.
- Executable output locations are separated from artifact output locations where supported.
- Inputs are mounted read-only.
- Symlink, hardlink, device-node, and traversal attacks are checked during staging and collection.
- Special files, sockets, and FIFOs are rejected from publication outputs unless schema-authorized.
- Archive extraction enforces file-count, expanded-size, nesting-depth, and path constraints.
- Secrets are injected only through short-lived mechanisms and are not included in image layers or provenance payloads.
- Swap is disabled for sensitive workloads or encrypted according to policy.
- Collected outputs pass malicious-content scanning (Section 16) before entering artifact storage.

### 11.7 Cgroups v2 resource controls

Every execution is placed in a dedicated cgroup v2 subtree with explicit limits:

- CPU quota and period;
- CPU weight;
- cpuset placement where deterministic performance is required;
- memory maximum;
- memory high threshold;
- optional memory minimum for reserved critical jobs;
- swap maximum;
- PID maximum;
- block I/O weight;
- per-device I/O bandwidth or IOPS limits where supported;
- huge-page limits;
- RDMA limits where applicable.

Resource classes define bounded defaults:

| Class | CPU | Memory | PIDs | Ephemeral storage | Wall time | Network |
|---|---:|---:|---:|---:|---:|---|
| `XS` | Small burst | Small | Low | Small | Short | Denied |
| `S` | Limited | Moderate | Low | Moderate | Short | Denied by default |
| `M` | Moderate | Moderate | Moderate | Moderate | Bounded | Grant required |
| `L` | High | High | Moderate | High | Bounded | Grant required |
| `CUSTOM` | Reviewed | Reviewed | Reviewed | Reviewed | Reviewed | Explicit |

Exact values are deployment policy, not user-controlled defaults.

### 11.8 Termination and cleanup

Hive enforces:

- startup timeout;
- idle timeout;
- wall-clock deadline;
- graceful termination interval;
- forced termination after grace expiry;
- descendant process cleanup through cgroup kill;
- output collection limits;
- volume unmount and destruction;
- network policy removal;
- secret revocation;
- workspace deletion;
- cleanup verification.

Termination reason and peak resource use are recorded.

### 11.9 Out-of-memory behavior

- Workloads are limited within their own cgroups.
- The scheduler reserves node headroom.
- Memory pressure is monitored before admission.
- OOM events are attributed to the execution.
- Partial outputs are marked incomplete and never treated as successful evidence.
- Critical control-plane services run in protected cgroups separate from experiments.

### 11.10 Runtime security monitoring

Node-level eBPF or equivalent runtime detection (Falco-class tooling) continuously monitors for:

- unexpected process execution within workloads relative to declared command specifications;
- runtime-socket, metadata-service, and host-path access attempts;
- privilege-escalation syscall patterns and repeated seccomp denials;
- unexpected outbound connection attempts before network-policy enforcement drops them.

Runtime detections feed the alerting pipeline (Section 23) and may trigger automatic quarantine of the execution, subject to review. Runtime monitoring evidence is retained per audit policy and serves as continuous dynamic verification of the isolation model between formal DAST cycles.

---

## 12. Network sandboxing

### 12.1 Default policy

Experiment networking is denied by default.

A network grant must specify:

- purpose;
- destination identities;
- ports and protocols;
- DNS names and resolution policy;
- maximum bytes and requests;
- start and expiry times;
- whether responses may be retained;
- approving authority;
- classification and export compatibility.

### 12.2 Enforcement

Network isolation uses workload network namespaces plus node-level enforcement through an approved combination of:

- nftables or equivalent packet filtering;
- Kubernetes NetworkPolicy with a verified enforcing CNI;
- eBPF policy;
- authenticated egress proxy;
- service mesh only where it does not weaken isolation.

Kubernetes NetworkPolicy declarations without enforcement verification are insufficient. Network policy manifests are themselves subject to IaC scanning in CI (Section 14).

### 12.3 Mandatory blocks

Workloads cannot directly access:

- node management endpoints;
- cloud instance metadata services;
- container runtime APIs;
- cluster control planes;
- internal databases;
- link-local administrative services;
- peer workload networks;
- unauthorized DNS resolvers;
- public package registries, except through the governed pull-through proxy under an explicit grant (Section 13.5);
- tenant-external destinations not in the grant.

### 12.4 DNS and egress

- DNS uses a controlled resolver.
- Resolution results are logged without exposing sensitive query payloads beyond policy.
- DNS rebinding and destination drift are checked.
- Egress may be pinned to verified IP ranges or mediated through a proxy.
- TLS certificate validation is mandatory.
- Private certificate authorities are explicitly configured.
- Raw sockets and packet capture are denied.
- Inbound connectivity is denied unless the execution protocol explicitly requires a brokered callback.

### 12.5 Exfiltration controls

For sensitive workloads:

- all egress is proxied;
- request and response sizes are bounded;
- destinations are allowlisted;
- uploads may require content inspection;
- covert-channel risk is documented rather than claimed to be eliminated;
- high-risk workloads use `OFFLINE_STRICT`.

Network grants and actual destination summaries are included in execution provenance.

---

## 13. Software supply chain: images, dependencies, signing, and distribution

### 13.1 SBOM requirements

- Every container image, platform component release, and experiment dependency closure carries a Software Bill of Materials in CycloneDX (default) or SPDX, per federation profile; the format is declared, never guessed.
- Two SBOM classes are distinguished and both retained:
  - **build-time SBOM**, emitted by the build pipeline from resolved lockfiles and build inputs;
  - **analysis SBOM**, produced by post-build image inspection, used to detect drift between declared and actual contents.
- Divergence between build-time and analysis SBOMs beyond policy tolerance fails admission.
- SBOMs are signed and attached to images as OCI referrer artifacts; SBOM digests are recorded in execution provenance and in `PublicationPackage` manifests.
- Model artifacts carry an ML-BOM (CycloneDX ML profile or equivalent) per Section 16.4.
- SBOM completeness (component identity, version, license, hash, supplier where known) is enforced by `SBOMCompletenessGate`.

### 13.2 Signing, attestations, and transparency

- Image and artifact signing uses Sigstore Cosign. Deployments choose, per federation profile:
  - **keyless signing** via Fulcio with OIDC workload identity and Rekor transparency-log inclusion; or
  - **keyed signing** with HSM- or KMS-backed keys for air-gapped or policy-constrained environments, with an internal transparency log or signed offline verification bundles.
- Required in-toto attestation predicates per image:
  - SLSA provenance;
  - SBOM attestation;
  - vulnerability scan result attestation (scanner, database version, timestamp);
  - VEX statement reference where applicable.
- SLSA targets: **Build L3** for RAE-Suite platform components; **Build L2 minimum** for experiment images, with L3 required for `STRICT` and `OFFLINE_STRICT` workloads.
- Verification occurs at **every** trust boundary:
  1. cluster admission (Sigstore policy-controller, Kyverno, or equivalent);
  2. Hive execution admission (`ImageSignatureGate`, `ImageAttestationGate`) — independent of cluster admission, so a bypassed or misconfigured cluster controller does not silently disable verification;
  3. CMT import verification for federated image references;
  4. offline evidence verification (Section 20).
- Rekor inclusion proofs (or offline bundle equivalents) are stored with provenance so verification does not depend on log availability at verification time.
- Signature verification policy (trusted identities, issuers, key sets) is versioned, journaled, and cannot be weakened through normal project administration.

### 13.3 Image requirements

Every image must be:

- pinned by immutable digest;
- built through an approved pipeline with hermetic builds where the ecosystem supports them;
- based on an approved minimal base image (distroless-class where practical) with a defined patch cadence and end-of-life tracking;
- signed and attested per 13.2;
- accompanied by build-time and analysis SBOMs;
- scanned for known vulnerabilities, malware, and prohibited packages at build, at admission, and continuously thereafter (Section 15);
- free of embedded secrets (layer-level secret scanning);
- minimal and free of unnecessary package managers or shells where practical.

Mutable tags are informational only and never used as execution identity.

### 13.4 Dependency controls

- Lockfiles are mandatory where the ecosystem supports them.
- Hash verification is required for fetched packages.
- Runtime dependency fetching is denied unless a network grant permits it, and even then only via the governed proxy.
- Dependency caches are read-only to workloads and partitioned by trust policy.
- Cache entries are content-addressed, scanned, and never trusted solely because they are cached.
- License and export-control policy is checked against SBOM data before sealing publication outputs.

### 13.5 Registry and ecosystem governance

- All package and image retrieval flows through private registries or an authenticated pull-through proxy; direct upstream access from build or workload environments is denied.
- Newly seen upstream packages and versions enter a policy-defined quarantine window with automated scanning before general availability.
- Dependency-confusion defenses: internal package namespaces are reserved and published upstream where registries permit; resolvers are pinned to scoped registries; internal-name resolution from public indexes is blocked.
- Typosquatting and starjacking heuristics run against newly requested packages; suspicious requests are held for review.
- Registry access, promotion, and quarantine decisions are journaled.

### 13.6 Platform distribution integrity

- RAE-Suite releases (binaries, images, Helm charts, verifier tooling) are distributed through a TUF-secured update channel or an approved equivalent providing role separation, threshold signing, rollback protection, and freshness guarantees.
- Release manifests are signed; consuming deployments verify before upgrade.
- The offline evidence verifier (Section 20.4) is itself distributed with reproducible-build verification where feasible, since a compromised verifier defeats the evidence model.

### 13.7 Admission and revocation

Images or dependencies may be denied because of:

- signature or attestation failure;
- missing or incomplete SBOM;
- missing provenance;
- vulnerabilities exceeding policy thresholds without an approved VEX justification;
- prohibited imports;
- malware detection;
- incompatible license;
- end-of-life runtime or base image;
- unapproved base image;
- policy revocation.

Already sealed evidence remains auditable; later findings are attached through `SecurityAdvisory` artifacts and `AFFECTED_BY` edges rather than mutation.

---

## 14. Application security pipeline (SAST, SCA, DAST, fuzzing)

### 14.1 Principles

- Security testing is continuous and pipeline-integrated, not release-adjacent.
- Findings from all tools converge into one triage backlog with severity SLAs (Section 15.3).
- Constitutional invariants are enforced twice: left-shifted in CI, and authoritatively at Tribunal gates. CI failure is advisory to developers; gate failure is blocking. The rule packs are shared so they cannot drift.

### 14.2 Static analysis (SAST)

- SAST runs on every merge request across all platform languages, with taint/dataflow analysis for injection, deserialization, path handling, and authorization flaws.
- Blocking thresholds: unresolved high/critical findings block merge to protected branches; exceptions require named authority, expiry, and journaled justification.
- Custom rule packs encode RAE constitution checks: absolute-path construction, traversal-capable path joins, prohibited imports (e.g., disallowed embedding libraries), unsafe deserialization primitives, secret-material patterns, and direct hash-algorithm selection outside the profile registry.
- Infrastructure-as-code scanning covers Kubernetes manifests, Helm charts, Terraform, seccomp/AppArmor profiles, and network policies — the artifacts that *implement* Sections 11–12 are treated as security-critical code.
- SAST tool versions and rule-pack digests are recorded; results are attached to release evidence.

### 14.3 Software composition analysis (SCA)

- SCA runs on every lockfile change and nightly against advisory feeds.
- Reachability analysis is used where available to distinguish present from invoked vulnerable code, feeding VEX justifications.
- License scanning is SBOM-driven and policy-gated.

### 14.4 Secret hygiene

- Pre-commit hooks and server-side push protection block credential patterns.
- CI scans diffs; scheduled jobs scan full repository history.
- Verified leaked secrets trigger an automated revocation runbook: rotate, journal, assess exposure window, notify owners.
- The Tribunal `SecretMaterialGate` remains the authoritative backstop for artifact payloads.

### 14.5 Dynamic analysis (DAST)

- Authenticated DAST runs against staging environments on a schedule and before every release candidate, covering the RAE-CRL API, A2A Bridge endpoints, CMT endpoints, and reviewer interfaces.
- API fuzzing is derived automatically from versioned OpenAPI and CBOR schemas: malformed encodings, boundary values, authorization-matrix probing (cross-tenant, cross-project, role confusion), and idempotency-key abuse.
- A standing **CMT adversarial harness** exercises downgrade attempts, replay, malformed manifests, chunk-corruption, consent-mismatch, oversized transfers, and hash-profile confusion — maintained as regression infrastructure, not one-off tests.
- Container-escape and isolation regression suites (Section 25.2) are treated as dynamic security testing and run in CI against representative node images.

### 14.6 Continuous fuzzing

- Coverage-guided fuzzing runs continuously (OSS-Fuzz-style infrastructure) for:
  - the deterministic CBOR codec (with differential fuzzing against an independent implementation);
  - schema validators;
  - archive and scientific-format handling (extraction limits, HDF5/notebook parsers);
  - CMT manifest parsing and chunk assembly;
  - evidence-package manifest parsing in the offline verifier.
- Corpora are versioned; crashes have triage SLAs; security-relevant crashes enter the vulnerability process (Section 15).
- Release gates require a minimum recent fuzzing budget with zero unresolved security-relevant crashes.

### 14.7 Memory safety

- New trust-critical components (codec, verifier, CMT transport) prefer memory-safe languages; unavoidable unsafe code is isolated, documented, and receives targeted review and sanitizer coverage (ASan/UBSan/MSan) in CI.

---

## 15. Vulnerability management, VEX, and coordinated disclosure

### 15.1 Continuous rescanning

- Admitted images and their SBOMs are rescanned continuously against updated advisory databases — admission is not immunity.
- New findings against images referenced by active projects raise journaled events and, where thresholds are exceeded, trigger execution-policy revocation for *future* runs.
- New findings against images referenced by **sealed evidence** generate `SecurityAdvisory` artifacts linked via `AFFECTED_BY` edges; sealed history is never mutated, but its security posture is kept honest.
- Scanner identity, database version, and scan timestamp are recorded so “clean” claims are always time-bounded.

### 15.2 Prioritization

Triage severity combines:

- CVSS base and environmental scoring;
- CISA KEV (known exploited) status;
- EPSS exploitation probability;
- SCA reachability and deployment exposure (internet-facing, sandbox-adjacent, control-plane);
- classification of data the component can touch.

### 15.3 Remediation SLAs

Deployment policy defines maximum remediation or mitigation windows by adjusted severity (e.g., critical-exploited measured in days, not weeks). SLA breaches escalate to accountable control owners and are visible in ISO-aligned control evidence. Exceptions require VEX-grade justification with expiry.

### 15.4 VEX

- The platform issues VEX statements (OpenVEX or CSAF, per profile) for its own releases: for each relevant advisory, a machine-readable status of `not_affected`, `affected`, `fixed`, or `under_investigation`, with justification.
- Tribunal vulnerability-gate exceptions are expressed as VEX statements, signed, journaled, and time-bounded.
- Publication packages include or reference the VEX set applicable to their execution closure at seal time (Section 20.1).

### 15.5 PSIRT and coordinated vulnerability disclosure

- A Product Security Incident Response Team function owns intake, triage, embargo handling, fix coordination, CVE assignment where applicable, and advisory publication.
- A public CVD policy and `security.txt` define reporting channels, safe-harbor scope, and response-time commitments.
- Advisories are signed, distributed through the TUF release channel and federation notices, and represented internally as `SecurityAdvisory` artifacts so affected tenants and packages are machine-discoverable.
- Federation peers receive advisory notices affecting artifacts they imported via CMT, under the same signed-event mechanism as revocations.

---

## 16. Content and data supply-chain security for scientific artifacts

### 16.1 Threat framing

In scientific exchange, *data is code*: notebooks execute, pickles deserialize into arbitrary code, and crafted binary scientific formats exploit parser vulnerabilities. CMT federation makes ingested content a cross-organizational attack vector.

### 16.2 Malicious-content scanning

- All ingested artifacts, experiment outputs entering artifact storage, and CMT-received payloads pass malicious-content scanning: signature-based malware detection plus format-aware structural validation.
- Findings quarantine the content (`QUARANTINED` state) pending review; scan verdicts, scanner versions, and database versions are journaled.
- Scanning is re-run when detection capabilities materially improve, with `SecurityAdvisory` linkage for late detections in sealed content.

### 16.3 Unsafe deserialization policy

- Raw pickle, joblib, and equivalent arbitrary-code deserialization formats are rejected as data artifacts by default (`UnsafeDeserializationGate`).
- Safe formats (e.g., safetensors for model weights, schema-validated columnar/array formats) are the required default.
- Reviewed exceptions require: named authority, expiry, documented necessity, and execution restricted to `HARDENED` or stronger profiles with no network grant during deserialization.
- Notebooks are sanitized on ingestion (output stripping per policy, metadata validation) and execute only inside Hive sandboxes, never in control-plane or reviewer contexts.

### 16.4 ML-BOM and model provenance

Model artifacts record:

- weights digest and serialization format;
- ML-BOM (framework, architecture identifiers, license);
- training-data references as sealed manifests or declared external provenance;
- evaluation provenance where claims depend on it;
- known-limitation and poisoning-risk declarations, stated honestly rather than omitted.

### 16.5 Dataset provenance

- Large datasets are referenced through sealed, chunk-hashed manifests.
- Origin, collection method, license, and transformation lineage are recorded through typed edges.
- Data-poisoning risk for externally sourced datasets is documented as a residual risk in dependent evidence, not silently ignored.

---

## 17. Execution provenance

An `Experiment` execution records distinct identifiers rather than a non-standard “pod digest”:

- source commit and tree identifier;
- sealed patch CID if applicable;
- image digest;
- image signature, attestation, and transparency-log inclusion references;
- SBOM digests (build-time and analysis);
- vulnerability scan reference (scanner, database version, timestamp, result digest);
- applicable VEX references;
- runtime type and version;
- runtime specification digest;
- seccomp profile digest;
- mandatory-access-control policy digest;
- cgroup resource policy digest;
- network-grant digest;
- input version CIDs;
- environment allowlist digest;
- command or workflow specification digest;
- execution start and end;
- exit status and termination reason;
- peak CPU, memory, PID, I/O, storage, and network usage;
- output manifest CID;
- output content-scan verdict reference;
- log manifest CID;
- node attestation where required.

Hostnames, raw node paths, and unnecessary infrastructure identifiers are omitted from portable evidence.

---

## 18. Scheduler, performance, and capacity governance

### 18.1 Admission control

Hive performs admission based on:

- tenant quota;
- project quota;
- requested resource class;
- current node capacity;
- security-profile availability;
- image readiness and verification status;
- data locality;
- classification constraints;
- deadline and priority;
- fairness policy.

A job is queued rather than overcommitting beyond configured safety margins.

### 18.2 Fairness and noisy-neighbor protection

- Weighted fair queuing is applied per tenant.
- Per-project concurrency is bounded.
- Strict workloads have separate capacity pools when required.
- Control-plane resources are isolated from experiment resources.
- CPU throttling, memory pressure, I/O latency, and queue delay are measured.
- Repeatedly abusive workloads may be quarantined automatically, subject to review.

### 18.3 Backpressure

Backpressure applies to:

- artifact ingestion;
- observation batches;
- graph expansion;
- embedding or indexing jobs;
- conflict generation;
- evidence package creation;
- content and vulnerability scanning queues;
- CMT transfer;
- experiment submission.

Clients receive stable retry semantics and bounded retry intervals. Unbounded internal queues are prohibited.

### 18.4 Artifact and query limits

Policy defines limits for:

- artifact payload size;
- edge count per version;
- batch size;
- archive expansion ratio;
- graph depth and visited nodes;
- query execution time;
- result count;
- publication package size;
- log volume;
- observation rate.

Large datasets are referenced through sealed manifests and chunked objects rather than embedded in a single artifact.

### 18.5 Caching

- Caches are content-addressed.
- Cache keys include tenant or sharing policy, classification, schema, tool version, and relevant execution policy.
- Sensitive cache entries are encrypted and access-controlled.
- Cross-tenant cache reuse is disabled unless content is public and policy explicitly permits it.
- Cache hits are recorded in provenance.
- Cache eviction never deletes the authoritative artifact or journal.

### 18.6 Performance targets

Initial service objectives:

- API availability measured separately from experiment capacity;
- bounded p95 and p99 latency for artifact metadata operations;
- bounded seal latency excluding required human review;
- bounded content- and vulnerability-scan latency budgets so security scanning does not become an unbounded ingestion bottleneck;
- conflict scans processed within a declared freshness window;
- scheduler queue time reported by resource class;
- journal durability and projection lag monitored continuously;
- no experiment-induced control-plane outage in isolation testing.

Numeric objectives are set per deployment after representative load tests.

---

## 19. RAE-Mesh and Consensual Memory Transfer

### 19.1 Peer identity

Each peer has:

- organization identity;
- node identity;
- signing and encryption keys;
- trust policy;
- supported schemas;
- canonicalization and hash profile;
- classification mapping;
- retention capabilities;
- content-safety scanning capabilities declaration;
- transport endpoints;
- revocation information.

Peer trust is not inferred from network location alone.

### 19.2 CMT protocol

CMT uses the following phases:

1. **Discover:** Exchange signed capabilities and policy profiles.
2. **Offer:** Sender provides a signed manifest, classification, purpose, terms, dependency summary, and applicable SBOM/advisory references for executable or model content.
3. **Evaluate:** Recipient checks authorization, compatibility, retention, classification, and capacity.
4. **Consent:** Recipient signs acceptance for exact manifest roots and terms.
5. **Transfer:** Encrypted, resumable, chunked content transfer.
6. **Verify:** Recipient validates hashes, signatures, schemas, edges, evidence, and runs malicious-content scanning per Section 16 before commit.
7. **Commit:** Recipient atomically imports or rejects the package.
8. **Receipt:** Recipient signs the accepted manifest and resulting local references.
9. **Reconcile:** Peers exchange missing events, conflict information, and security advisories under policy.

### 19.3 Capability tokens

Tokens are:

- audience-bound;
- sender- and recipient-bound;
- purpose-bound;
- tenant- and project-scoped;
- artifact- or manifest-scoped;
- short-lived;
- nonce-protected;
- signed;
- optionally proof-of-possession bound.

Bearer tokens with broad artifact access are prohibited.

### 19.4 Revocation semantics

Revocation can:

- stop future synchronization;
- revoke future key access;
- revoke capability tokens;
- mark imported data as prohibited for further use;
- request deletion;
- obtain deletion attestations;
- propagate revocation and security-advisory notices.

Revocation cannot guarantee recall of plaintext already disclosed or copied outside enforceable controls. Agreements and audit evidence address that residual risk.

### 19.5 Conflict and merge handling

- Sealed versions are never overwritten.
- Concurrent versions remain distinct.
- A merge creates a new artifact version with explicit source edges.
- Classification never decreases automatically.
- Policy incompatibility causes quarantine, not lossy coercion.
- Unknown schemas are retained only in a quarantined opaque form when policy allows it.
- Tombstones, revocations, and security advisories are synchronized as signed events.

### 19.6 Transfer security

- Mutual authenticated transport is mandatory.
- Application-level signatures remain required even when transport is secure.
- Payload encryption may be recipient-specific.
- Chunk hashes are verified before assembly.
- Decompression and archive limits are enforced.
- Transfer rate, storage, and concurrency quotas prevent denial of service.
- Replay protection uses transfer identifiers, nonces, expiry, and receipt state.
- The CMT adversarial harness (Section 14.5) is maintained as permanent regression infrastructure against downgrade, replay, and malformed-manifest attacks.

---

## 20. Evidence and publication packages

### 20.1 Package contents

A `PublicationPackage` contains a canonical manifest covering:

- root artifact version CIDs;
- selected dependency closure;
- artifact schemas;
- edge vocabulary version;
- execution provenance;
- SBOM digests for every image in the execution closure;
- ML-BOM references for included model artifacts;
- applicable VEX statements or references at seal time;
- vulnerability scan references (scanner, database version, timestamp) — an explicit, time-bounded **security-posture-at-seal declaration**;
- linkage instructions for post-publication `SecurityAdvisory` lookups;
- reviews and Tribunal outcomes;
- relevant Trace checkpoints;
- signatures;
- transparency-log inclusion proofs or offline bundles;
- timestamp tokens;
- public-key and certificate references;
- revocation-status evidence;
- hash and canonicalization profile;
- verification instructions;
- omitted-content declarations;
- legal and classification terms.

### 20.2 Signatures

Signatures bind:

- domain separator;
- federation profile;
- tenant and project;
- package manifest CID;
- signer identity;
- signing purpose;
- signature time;
- key identifier;
- schema version.

Detached JWS, COSE signatures, or Sigstore bundle formats may be used by profile. The format must be explicit.

### 20.3 Timestamping

RFC 3161 timestamps are supported when the timestamp authority accepts the selected digest profile.

If the authority requires a different approved digest:

- a timestamp-specific digest is declared explicitly;
- the token binds the canonical package manifest;
- verifiers are never expected to guess the algorithm;
- the package retains the canonical source CID.

Timestamping supplements signatures, transparency-log inclusion, and journal chronology; it does not replace them.

### 20.4 Offline verification

The verifier can:

1. parse the canonical manifest;
2. validate schemas;
3. recompute CIDs;
4. verify version chains and graph closure;
5. verify signatures, attestations, transparency-log inclusion proofs, and timestamps;
6. evaluate key status at signing time;
7. validate SBOM digests against referenced images where images are available;
8. report the seal-time security posture and, when the verifier explicitly requests network access, retrieve current advisory and VEX status for the closure;
9. identify missing, tombstoned, or redacted content;
10. produce a machine-readable verification report distinguishing "cryptographically intact" from "currently free of known vulnerabilities" — these are different claims and are never conflated.

Verification tooling uses project-relative inputs and does not require network access unless the verifier explicitly requests live revocation or advisory data. The verifier is distributed through the integrity-protected channel of Section 13.6.

---

## 21. API and A2A Bridge

### 21.1 API principles

- Versioned schemas and endpoints
- Idempotency keys for mutation commands
- Optimistic concurrency for draft updates
- Cursor-based pagination
- Bounded filtering and graph traversal
- Explicit consistency semantics
- Stable error codes
- Request and response size limits
- Rate limiting by principal, tenant, project, and operation class
- Schema-derived DAST and API fuzzing as standing regression coverage (Section 14.5)

### 21.2 Core operations

The API supports:

- create and update draft;
- submit for review;
- seal version;
- retrieve artifact or version;
- query bounded provenance;
- register review;
- propose and disposition conflict;
- submit and cancel experiment;
- retrieve execution status and manifests;
- construct and verify evidence package;
- query security advisories and VEX status for artifacts and packages;
- negotiate and execute CMT;
- apply legal hold or disposition;
- retrieve audit events subject to authorization.

### 21.3 A2A messages

Every A2A message includes:

- message identifier;
- correlation and causation identifiers;
- sender and intended role;
- tenant and project;
- schema version;
- expiry;
- payload digest;
- authorization context;
- signature or authenticated channel binding;
- trace context without sensitive payload leakage.

Messages are validated before dispatch and captured through the journal or transactional log bridge.

### 21.4 Idempotency and retries

- Commands are idempotent within a defined window.
- Consumers record processed message identifiers.
- Retries use bounded exponential backoff.
- Poison messages enter quarantine.
- At-least-once delivery must not create duplicate artifacts, executions, or transfers.

---

## 22. Storage and resilience

### 22.1 Storage separation

The architecture separates:

- append-only event journal;
- artifact metadata;
- immutable object payloads;
- current-state projections;
- search indexes;
- execution logs;
- cryptographic keys;
- backups.

Compromise of a search index must not permit authoritative history rewriting.

### 22.2 Encryption

- Data is encrypted in transit and at rest.
- Tenant-specific or classification-specific keys are used where required.
- Key access is policy-controlled and audited.
- Key rotation does not alter artifact CIDs.
- Envelope encryption supports cryptographic erasure.
- Secrets are stored outside artifact payloads.

### 22.3 Backup and recovery

Backups are:

- encrypted;
- immutable for a policy-defined window;
- tested through restoration drills;
- protected from the same administrative plane where practical;
- accompanied by journal consistency checks;
- classified and retained like source data.

Recovery validates event-chain continuity and rebuilds projections from authoritative records.

### 22.4 Availability design

- Journal and metadata stores use quorum or equivalent durability appropriate to the deployment.
- Split-brain writes are rejected or reconciled through explicit version creation.
- Object uploads use staging and atomic manifest publication.
- Control-plane degradation does not grant weaker sandbox policy or disable signature verification.
- Fail-open authorization, fail-open network policy, and fail-open supply-chain verification are prohibited.

---

## 23. Observability and audit

### 23.1 Metrics

Required metrics include:

- API latency and error rate;
- journal commit latency;
- projection lag;
- gate denial counts by reason code;
- signature and attestation verification failures at each trust boundary;
- SBOM drift detections;
- vulnerability rescan findings, open counts by severity, and SLA compliance;
- fuzzing coverage and unresolved crash counts;
- content-scan quarantine rates;
- graph query cost;
- conflict precision and reviewer disposition;
- queue depth and wait time;
- experiment startup time;
- CPU throttling;
- memory pressure and OOM events;
- PID exhaustion;
- storage and I/O throttling;
- network grant use and denied flows;
- runtime-detection event rates;
- cleanup failures;
- CMT throughput and verification failures;
- evidence verification outcomes.

### 23.2 Logs and traces

- Structured logs use correlation identifiers.
- Payload bodies are omitted by default.
- Classification labels control telemetry export.
- Tokens, keys, environment secrets, and sensitive prompts are redacted.
- Trace sampling never bypasses security-event capture.
- Clock synchronization health is monitored.
- Audit events have longer, policy-controlled retention than ordinary diagnostics.

### 23.3 Alerting

Alerts cover:

- journal integrity failure;
- unauthorized policy change;
- signature-verification bypass indicators (e.g., workloads admitted without gate evidence);
- sandbox escape indicators;
- unexpected host namespace access;
- runtime-socket access attempts;
- repeated seccomp violations;
- metadata-service access attempts;
- abnormal egress;
- registry quarantine bypass attempts and dependency-confusion indicators;
- new critical/KEV findings against active images;
- cleanup failure;
- cross-tenant authorization denial spikes;
- signature or timestamp verification failure;
- projection inconsistency;
- backup restoration failure.

---

## 24. Security governance and ISO/IEC 27001 alignment

The platform produces evidence supporting controls in areas such as:

- asset inventory (including SBOM-derived software inventory);
- identity and access management;
- cryptographic controls;
- secure development (SAST/DAST/fuzzing records, review evidence);
- supplier and dependency management (registry governance, SLSA/attestation records);
- logging and monitoring;
- incident management (PSIRT records, advisory history);
- backup and continuity;
- data classification;
- retention and deletion;
- vulnerability management (rescan history, SLA compliance, VEX records);
- change control.

Each deployment must still establish:

- an ISMS scope;
- risk assessment;
- statement of applicability;
- accountable control owners (including a named owner for vulnerability management and PSIRT);
- operating procedures;
- internal audits;
- management review;
- corrective actions.

The software does not itself confer certification.

---

## 25. Testing and assurance

### 25.1 Functional testing

- Schema compatibility
- Version-chain correctness
- Event atomicity
- Lifecycle transitions
- Edge grammar and cycle detection
- Classification propagation
- Conflict disposition
- Evidence construction and verification
- Advisory linkage and VEX status resolution
- CMT replay and reconciliation

### 25.2 Isolation testing

Automated tests attempt:

- host filesystem access;
- host namespace joining;
- privilege escalation;
- capability acquisition;
- runtime-socket access;
- device access;
- metadata-service access;
- DNS rebinding;
- unauthorized egress;
- registry-proxy bypass;
- fork bombs;
- memory exhaustion;
- storage exhaustion;
- decompression bombs;
- malicious deserialization payload delivery through data artifacts;
- symlink and hardlink escape;
- process survival after cancellation;
- cross-tenant cache access;
- side-channel indicators within the stated threat model.

### 25.3 Performance testing

- Burst artifact ingestion
- Large observation batches
- Deep but bounded graph queries
- Conflict scan throughput
- Content- and vulnerability-scan throughput under ingestion load
- Concurrent experiment startup
- CPU, memory, PID, and I/O contention
- Image pull storms
- CMT transfer saturation
- Projection rebuild
- Backup restoration
- Evidence-package verification at scale

### 25.4 Security assurance

- Threat modeling before each major release, including supply-chain and data-as-code threat trees
- SAST, SCA, IaC scanning, and secret scanning as standing CI gates (Section 14)
- Scheduled and pre-release DAST with authenticated coverage of all externally reachable surfaces
- Continuous coverage-guided fuzzing with corpus governance and crash SLAs
- Dependency, image, and layer scanning at build, admission, and continuously post-admission
- Signature/attestation verification testing at every trust boundary, including deliberate bypass attempts
- Penetration tests, including registry, CI/CD, and signing-infrastructure scope — the build pipeline is in scope, not just the product
- Container escape review
- Policy bypass testing
- Key-compromise and signing-identity-compromise exercises, including transparency-log-assisted detection drills
- Disaster-recovery exercises
- Independent review for strict isolation profiles and for the canonical codec and offline verifier

---

## 26. Delivery roadmap

A cross-cutting **Security Engineering Track (Track S)** runs through all phases: CI security gates, fuzzing infrastructure, scanning pipelines, and PSIRT operations are built alongside features, not appended afterward. Phase exit criteria include Track S items.

### Phase 0 — Architecture, threat-model, and pipeline-security freeze

Deliverables:

- canonical schemas;
- deterministic CBOR test vectors;
- hash profile specification;
- identity and principal model;
- edge grammar;
- classification lattice;
- workload threat model;
- CMT threat model;
- supply-chain threat model (build, registry, distribution, data-as-code);
- constitutional gate registry;
- **Track S:** signing infrastructure decision (keyless vs. keyed per profile), SBOM format profile, CI SAST/SCA/secret-scanning baseline live on all repositories, CVD policy and security.txt published.

Exit criteria:

- no unresolved version-chain ambiguity;
- no mutable authoritative envelope fields;
- approved trust boundaries;
- test vectors independently reproducible;
- CI blocks unresolved high/critical SAST and secret findings on protected branches.

### Phase 1 — Epistemic core

Deliverables:

- artifact draft and seal service;
- append-only journal;
- lifecycle projections;
- typed graph validation;
- classification enforcement;
- baseline Tribunal gates including `SecretMaterialGate` and shared CI/Tribunal rule packs;
- project-relative URI validator;
- **Track S:** continuous fuzzing live for the CBOR codec and schema validators; differential codec testing.

Exit criteria:

- every successful transition has a durable event;
- projections rebuild from the journal;
- sealed versions are immutable;
- graph and information-flow tests pass;
- codec fuzzing shows no unresolved security-relevant crashes.

### Phase 2 — Hive isolation and supply-chain admission baseline

Deliverables:

- rootless OCI execution;
- namespace isolation;
- capability removal;
- seccomp and mandatory-access-control profiles;
- read-only filesystems;
- cgroups v2 resource classes;
- wall-time enforcement;
- default-deny networking;
- source and output staging;
- execution provenance including SBOM and signature references;
- **Track S:** private registry and pull-through proxy with quarantine; Cosign signing in build pipeline; signature/SBOM/attestation verification at cluster admission **and** Hive execution admission; build-time vs. analysis SBOM drift detection; `MaliciousContentGate` and `UnsafeDeserializationGate` operational.

Exit criteria:

- isolation test suite passes;
- fork, memory, PID, storage, and network abuse remain workload-scoped;
- no runtime sockets or host mounts are exposed;
- cleanup is verified after forced termination;
- unsigned or SBOM-less images cannot execute by any path, verified by deliberate bypass testing.

### Phase 3 — Hardened and strict runtimes

Deliverables:

- gVisor or equivalent hardened runtime;
- Kata or microVM strict runtime;
- offline strict profile;
- encrypted ephemeral storage;
- scheduler placement by security class;
- node-pool separation;
- **Track S:** runtime security monitoring (eBPF/Falco-class) with alert integration; SLSA L3 build pipeline for platform components.

Exit criteria:

- untrusted workloads cannot select weaker profiles;
- runtime differences are captured in provenance;
- escape-oriented penetration testing has no unresolved critical finding;
- runtime detections fire correctly against the isolation regression suite.

### Phase 4 — Watchdog and Tribunal workflows

Deliverables:

- normalized proposition model;
- bounded contradiction operator;
- conflict candidate lifecycle;
- reviewer interfaces;
- benchmark and calibration suite;
- Kaizen tuning boundaries;
- **Track S:** continuous post-admission rescanning of images/SBOMs; `SecurityAdvisory` artifact type and `AFFECTED_BY` linkage; vulnerability triage with KEV/EPSS prioritization and SLAs; VEX issuance workflow.

Exit criteria:

- no automatic truth assertion;
- reviewer confirmation required;
- precision, recall, and reversal metrics available;
- alert volume remains within project quotas;
- a synthetic advisory correctly propagates to affected sealed evidence within the freshness window.

### Phase 5 — Evidence packages

Deliverables:

- canonical package manifest with SBOM, VEX, scan-reference, and transparency-proof fields;
- dependency closure builder;
- signatures and transparency-log inclusion proofs (or offline bundles);
- RFC 3161 integration;
- offline verifier including seal-time security-posture reporting;
- tombstone and redaction representation;
- **Track S:** verifier distributed via TUF-secured channel; verifier manifest parsing under continuous fuzzing.

Exit criteria:

- independent verifier reproduces package CIDs;
- malformed and incomplete packages fail closed;
- key and timestamp policy is explicit;
- verification report correctly distinguishes integrity claims from vulnerability-currency claims.

### Phase 6 — RAE-Mesh and CMT

Deliverables:

- peer capability exchange;
- manifest offer and consent;
- proof-of-possession tokens;
- resumable encrypted transfer;
- receipts;
- revocation, deletion-attestation, and advisory-propagation events;
- conflict-preserving merge;
- **Track S:** CMT adversarial harness as permanent regression infrastructure; content-safety scanning on all imports; DAST coverage of CMT endpoints.

Exit criteria:

- replay and downgrade tests pass;
- incompatible profiles fail safely;
- transfers are atomic;
- revocation semantics are accurately represented;
- a malicious payload injected in federation testing is quarantined before commit.

### Phase 7 — Scale, resilience, and operational assurance

Deliverables:

- quota and fairness scheduler;
- bounded graph query planner;
- capacity dashboards;
- projection rebuild automation;
- backup and restore drills;
- federation load tests;
- incident runbooks including PSIRT, secret-leak, and signing-key-compromise runbooks;
- ISO-aligned control evidence mapping including vulnerability-management and supply-chain evidence;
- **Track S:** full pre-release DAST cycle; pipeline-inclusive penetration test; signing-identity compromise exercise.

Exit criteria:

- control plane survives resource-abuse tests;
- recovery objectives are demonstrated;
- noisy-neighbor limits are effective;
- vulnerability SLA compliance is demonstrable over a sustained window;
- no critical unresolved security findings.

---

## 27. Release gates

A production release is blocked unless:

- canonical encoding test vectors pass across implementations;
- event and artifact integrity checks pass;
- all constitutional gates pass;
- isolation and network-abuse tests pass;
- resource limits are enforced through cgroups v2 or an approved equivalent;
- SAST has no unresolved high/critical findings without journaled, expiring exceptions;
- SCA and image scans show no vulnerabilities above policy threshold without approved VEX justification;
- secret scans of the release scope are clean;
- the release candidate has passed an authenticated DAST cycle against all external surfaces;
- continuous fuzzers have met the minimum recent CPU budget with zero unresolved security-relevant crashes;
- all shipped images are digest-pinned, Cosign-signed, attested (SLSA provenance and SBOM), and verified through the enforced admission path, with transparency-log inclusion proofs or offline bundles archived;
- build-time vs. analysis SBOM drift is within tolerance;
- deliberate signature-bypass attempts fail at both cluster and Hive admission;
- no privileged or host-namespace workload path exists;
- backup restoration has been demonstrated;
- evidence packages verify independently, including SBOM/VEX and posture reporting;
- CMT downgrade, replay, and malicious-import tests pass;
- VEX statements for the release are published and signed;
- release artifacts are distributed through the TUF-secured channel;
- documentation states residual risks without overstating guarantees.

---

## 28. Key residual risks

Even after implementation, the following remain:

- kernel or runtime zero-day vulnerabilities;
- side channels not eliminated by container isolation;
- malicious authorized insiders;
- compromised identity providers, signing keys, or transparency-log infrastructure;
- upstream supply-chain compromise that evades quarantine, scanning, and provenance checks before detection (novel or dormant implants);
- vulnerabilities disclosed after sealing — mitigated by continuous rescanning, advisories, and VEX, but never eliminated;
- data copied by an authorized federation recipient;
- data poisoning in externally sourced datasets despite provenance documentation;
- malicious content evading detection at ingestion time;
- semantic errors in ontology or contradiction normalization;
- false confidence from incomplete evidence;
- legal conflicts between jurisdictions;
- resource estimation errors for novel workloads.

Mitigations include strict runtime profiles, least privilege, verification at every trust boundary, transparency logging, continuous rescanning with advisory propagation, key rotation, independent review, federation contracts, offline execution, reproducibility checks, and transparent residual-risk reporting.

---

## 29. Definition of done

RAE-CRL 2.2 is complete when it can demonstrate that:

1. Every authoritative transition is append-only, attributable, and rebuildable.
2. Every sealed version binds its predecessor and canonical content.
3. Every artifact and derived output obeys classification flow.
4. Every experiment runs under an explicit isolation and resource profile.
5. Host namespaces, privileged mode, runtime sockets, and unrestricted egress are unavailable.
6. CPU, memory, PID, I/O, storage, wall-time, and concurrency abuse are bounded.
7. Execution provenance is sufficient to identify source, image, runtime, policy, inputs, outputs, SBOMs, and verification evidence.
8. No image or platform component executes without verified signatures, attestations, and SBOMs, and bypass attempts demonstrably fail.
9. Admitted software is continuously rescanned; post-seal findings propagate as linked, signed advisories without mutating history.
10. SAST, SCA, secret scanning, DAST, and continuous fuzzing operate as standing, gate-enforced pipeline controls with severity SLAs.
11. Scientific content is treated as a supply-chain vector: unsafe deserialization is gated, ingested content is scanned, and models carry ML-BOM provenance.
12. Conflict detection remains advisory until authorized confirmation.
13. Evidence packages verify independently and offline, carry SBOM/VEX and a time-bounded security-posture declaration, and never conflate integrity with vulnerability-currency.
14. CMT transfers are consensual, scoped, signed, replay-resistant, content-scanned, and honest about revocation limits.
15. Negative knowledge cannot be silently erased, while lawful disposition remains possible.
16. Quality Tribunal gates block non-compliant code, content, and artifacts before sealing or execution.
17. A functioning PSIRT and CVD process exists with signed, distributable advisories.
18. Recovery, isolation, supply-chain, and federation behavior have been tested under failure and adversarial conditions, with the build and signing pipeline explicitly in scope.
