# Report template

Fill every bracket. Remove sections that would be empty, except "Not assessed".

---

# Kubernetes security audit: [cluster context]

**Date:** [YYYY-MM-DD] · **Cluster:** [provider and version, e.g. EKS 1.30, or "n/a (manifest review)"] · **Scope:** [all namespaces / list] · **Mode:** [cluster / manifests / scanner output]

**Input:** [what actually ran: k8s-audit.sh, extra kubectl queries, rendered manifests, Kubescape, Trivy]. Read-only; nothing was changed.

## Summary

| Critical | High | Medium | Low |
|---|---|---|---|
| [n] | [n] | [n] | [n] |

[Two or three sentences: the overall picture in plain words. The worst path an
attacker has, and how far the top 3 fixes close it.]

## Fix first (this week)

1. [Action] ([finding ID]). [Effort, downtime yes/no.]
2. [Action] ([finding ID]). [Effort, downtime yes/no.]
3. [Action] ([finding ID]). [Effort, downtime yes/no.]

## Findings

### F-01 · [Severity] · [Title]

- **Where:** [namespace/kind/name, counts]
- **Why it matters:** [what an attacker gets, one or two sentences]
- **References:** CIS [id or -] · SOC 2 [criteria] · ISO 27001:2022 [control]

**Fix:**

```yaml
[adapted snippet]
```

[Rollout note if the fix can break traffic or deploys.]

[Repeat for each Critical and High finding. Medium and Low may go in the table
below with a one-line fix each.]

### Other findings

| ID | Severity | Finding | Fix | CIS | SOC 2 | ISO |
|---|---|---|---|---|---|---|
| F-0x | Medium | [finding] | [one line] | [id] | [criteria] | [control] |

## Expected privileges (verify, not findings)

| Workload | What it has | Why it is usually needed | Check |
|---|---|---|---|
| [kube-system/aws-node] | [hostNetwork] | [CNI] | [matches vendor docs?] |

## Not assessed

[Everything you could not see and why: managed control plane settings, node
OS, image vulnerabilities if Trivy was not available, runtime detection, backup
and restore. For each, the setting or question to verify.]

## About this report

Generated with the open-source k8s-security-audit skill. It is an automated,
read-only review of what the inputs listed above show; it is not a
penetration test. CIS, SOC 2 and ISO 27001 references support an auditor
conversation and are not a certification.

For a human-reviewed audit with an evidence pack for your auditor, or
white-label reports for your clients: https://k8s-security.pro/audit-service
