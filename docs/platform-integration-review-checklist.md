# Platform Integration Review Checklist

## Product registry

- [ ] Every product ID is unique and stable.
- [ ] Product version and supported contract identifiers are current.
- [ ] Accepted classifications match the target product's actual access policy.
- [ ] Offline or degraded products are represented honestly.

## Artifact integrity

- [ ] Every artifact identifies its owning source product.
- [ ] Artifact and revision IDs match the source record.
- [ ] SHA-256 checksums were calculated from the transferred payload.
- [ ] Status and governance state reflect the current approved revision.
- [ ] Only independent value-bearing artifacts use `include_in_portfolio: true`.

## Decision cases

- [ ] Each case includes all material finance, evidence, intelligence, and computation artifacts.
- [ ] Required target products are declared.
- [ ] Decision packet and knowledge collection IDs are correct where applicable.
- [ ] Case confidence policy is appropriate for the decision.
- [ ] Blocking reasons have been reviewed rather than hidden.

## Dependencies

- [ ] Every required dependency is represented.
- [ ] Relationship labels describe the actual direction of influence.
- [ ] The graph is acyclic.
- [ ] Superseded artifacts are not treated as current inputs.

## Handoffs

- [ ] Source product owns the artifact revision.
- [ ] Target product accepts the classification.
- [ ] Completed handoffs have approved artifacts and governance where required.
- [ ] Payload hashes and destination IDs are retained.
- [ ] Rejections and failures include actionable error codes or notes.

## Portfolio interpretation

- [ ] Currency is consistent across aggregated artifacts.
- [ ] Derived artifacts are excluded from value aggregation.
- [ ] Confidence and downside probabilities have evidence and owners.
- [ ] Risk-adjusted value is not presented as a guaranteed outcome.
- [ ] Portfolio totals reconcile to the included artifact list.

## Publication and operations

- [ ] Integration manifest lists the expected products, cases, contracts, and API routes.
- [ ] Input, output, and dependency hashes reproduce.
- [ ] Workspace revision was saved before handoff or publication.
- [ ] Public interfaces do not reveal confidential or restricted details.
- [ ] Institutional owners approved the final decision outside the tool.
