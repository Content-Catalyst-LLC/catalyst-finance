# Evidence, Review, Governance, and Publication

Catalyst Finance v1.9.0 adds a governed publication layer above the financial models. It does not change a calculation merely because a reviewer comments on it. Instead, it preserves the referenced artifact and revision, records evidence and review activity, and compiles a reproducible publication record.

## Records

A governance definition can contain:

- assumptions with owners, confidence, applicability, review status, and evidence links;
- sources with citations, dates, ownership, applicability, access status, and privacy controls;
- evidence excerpts with locators and confidence;
- claims linked to metric paths, calculation identifiers, assumptions, sources, and evidence;
- methodology declarations, data-quality notes, conflicts, limitations, and excluded factors;
- private attachment metadata and SHA-256 checksums;
- append-only review requests, comments, findings, objections, revision requirements, resolutions, approvals, publication, and withdrawal events.

## Publication gate

A governed case is publishable only when it contains evidence, has at least one headline claim, fully traces every headline claim, has no unresolved finding, objection, or revision requirement, and has at least one approval. A requested `approved` or `published` state does not override this gate.

## Audit and reproducibility

Review events are compiled into a SHA-256 hash chain. The immutable run record stores the source artifact and revision identifiers, the model and version, the governance-definition hash, the redacted public-payload hash, and the head of the audit chain. Re-running the same definition with the same generation timestamp produces the same record.

## Redaction

Public publications must use `exclude_private`. Private sources, evidence, assumptions, review events, and attachments are removed. Claims marked non-public or dependent on private records are also removed. The private workspace record remains unchanged.

## Outputs

The CLI and API provide contract-valid JSON. The CLI also writes a claim trace CSV, Markdown decision brief, accessible PDF-ready HTML, and redacted public JSON. Handoff manifests preserve governance, artifact, revision, evidence, review, and methodology identifiers for Knowledge Library and Decision Studio.
