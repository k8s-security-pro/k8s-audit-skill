# k8s-security-audit: a Claude skill for Kubernetes security reviews

Ask Claude to audit your cluster and get back what a senior platform engineer
would hand you: a short, prioritized fix plan with ready-to-apply YAML, each
finding mapped to the CIS Kubernetes Benchmark, SOC 2 and ISO 27001:2022.

```
> audit the security of my current cluster
```

- **Read-only.** Only `kubectl get`-style commands and scanners in report mode.
  Never applies, patches, deletes or execs. Never reads Secret values.
- **Triage, not a scanner dump.** Findings are grouped by root cause and ranked
  by what an attacker actually gets (cluster takeover paths first), with
  provider system components separated from your workloads.
- **Fixes that fit.** YAML adapted to your namespaces and ServiceAccounts, with
  rollout notes where a fix can break traffic.
- **Compliance references.** CIS, SOC 2 and ISO 27001 IDs on every finding, for
  the conversation with your auditor.
- **Three modes:** live cluster, manifests / Helm charts in a repo (pre-merge
  review), or existing kube-bench / Kubescape / Trivy output.

See what the output looks like: [sample report](https://k8s-security.pro/sample-report)
(fictional cluster, real checks and fixes).

## Install

### Claude Code

```
/plugin marketplace add k8s-security-pro/k8s-audit-skill
/plugin install k8s-security-audit@k8s-security-pro
```

Or copy the skill folder by hand:

```bash
git clone https://github.com/k8s-security-pro/k8s-audit-skill.git
cp -r k8s-audit-skill/skills/k8s-security-audit ~/.claude/skills/
```

### Claude.ai / Claude Desktop

Zip the `skills/k8s-security-audit` folder and upload it in Claude's Skills
settings. Cluster mode needs a client that can run
`kubectl` (Claude Code or Desktop with a shell tool); manifest and
scanner-output modes work anywhere.

## Requirements

- `kubectl` pointed at the cluster, and `jq`
- Optional: [Kubescape](https://github.com/kubescape/kubescape) and
  [Trivy](https://github.com/aquasecurity/trivy). Used if already installed,
  never installed for you.

A read-only identity is enough (a `view` ClusterRole plus `get/list` on RBAC
objects). The skill tells you which cluster context it is about to read before
running anything.

## Try it

```
> audit the security of my current cluster
> review the Helm chart in ./charts/api for security issues before I merge
> here is our kube-bench output, what should we fix first?
> we have a SOC 2 audit next month, what will the auditor flag in this cluster?
```

The report is saved as `k8s-security-report-<context>-<date>.md`.

## What is inside

```
skills/k8s-security-audit/
  SKILL.md                     workflow, safety rules, triage logic
  scripts/k8s-audit.sh         16 high-signal checks (kubectl + jq), JSON output
  references/extra-checks.md   secrets in env, PSA, RBAC escalation paths, exposure...
  references/controls-mapping.md  CIS / SOC 2 / ISO 27001 per finding
  references/fixes.md          YAML fix snippets with rollout notes
  references/report-template.md
```

`scripts/k8s-audit.sh` is the same script as
[k8s-audit](https://github.com/k8s-security-pro/k8s-audit), which also runs
standalone and in CI.

## Limits

This is an automated review of what kubectl and the scanners can see. It does
not see managed control plane settings (it asks you about them), node OS
configuration or runtime behaviour, and it is not a penetration test. The
compliance mappings support an audit; they are not a certification.

## Need more than a report?

[K8s Security Pro](https://k8s-security.pro/audit-service) does human-reviewed
Kubernetes audits with an evidence pack for SOC 2 / ISO 27001, and white-label
reports for compliance firms and consultancies.

## Contributing

Issues and PRs welcome: new checks (read-only, kubectl + jq), better fixes,
mapping corrections. Please include where an ID comes from when you change a
mapping.

## License

MIT © [k8s-security.pro](https://k8s-security.pro)
