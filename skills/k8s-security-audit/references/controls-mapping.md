# Controls mapping

CIS = CIS Kubernetes Benchmark v1.8 section 5 (policies) and 3 (logging) item IDs.
Managed-service benchmarks (CIS EKS / GKE / AKS) renumber some items; if the user
is on a managed service and asks for those IDs, say the generic ID and that the
managed benchmark has an equivalent. SOC 2 = 2017 Trust Services Criteria
(revised points of focus 2022). ISO = ISO/IEC 27001:2022 Annex A.

These are references to support an auditor conversation, not proof of
compliance. Use "-" when there is no matching item; never invent one.

## Checks from scripts/k8s-audit.sh

The `#` numbers are the item numbers of the k8s-security.pro 50-point checklist
that the script covers (16 of 50), which is why they have gaps.

| Script check | Finding | CIS | SOC 2 | ISO 27001:2022 |
|---|---|---|---|---|
| #2 | Privileged containers | 5.2.2 | CC6.1, CC6.8 | A.8.9 |
| #3 | allowPrivilegeEscalation not disabled | 5.2.6 | CC6.8 | A.8.9 |
| #4 | Running as root (runAsNonRoot unset) | 5.2.7 | CC6.8 | A.8.9 |
| #4b | readOnlyRootFilesystem not set | - | CC6.8 | A.8.9 |
| #5 | hostPID / hostIPC / hostNetwork | 5.2.3, 5.2.4, 5.2.5 | CC6.1, CC6.8 | A.8.9 |
| #6 | ServiceAccount token auto-mounted | 5.1.6 | CC6.1 | A.5.15, A.8.2 |
| #7 | Capabilities not dropped (ALL) | 5.2.10 | CC6.8 | A.8.9 |
| #7b | Dangerous capabilities added (SYS_ADMIN, NET_ADMIN, NET_RAW...) | 5.2.8, 5.2.9 | CC6.8 | A.8.9 |
| #9 | hostPath volumes | 5.2.12 | CC6.1, CC6.8 | A.8.9 |
| #8 | Namespaces without a NetworkPolicy | 5.3.2 | CC6.6 | A.8.20, A.8.22 |
| #14 | cluster-admin bindings | 5.1.1 | CC6.1, CC6.3 | A.8.2, A.5.15 |
| #15 | Workloads using the default ServiceAccount | 5.1.5 | CC6.1 | A.5.15, A.8.2 |
| #16 | Roles with * verbs on * resources | 5.1.3 | CC6.3 | A.8.2 |
| #20 | Workloads in the default namespace | 5.7.4 | CC6.1 | A.8.9 |
| #22 | Containers without resource limits | - | A1.1 | A.8.6 |
| #28 | Images using :latest or untagged | - | CC8.1 | A.8.32 |

## Checks from references/extra-checks.md

| Finding | CIS | SOC 2 | ISO 27001:2022 |
|---|---|---|---|
| Secrets passed as environment variables | 5.4.1 | CC6.1, CC6.7 | A.5.17, A.8.12 |
| Literal credentials in env / ConfigMaps | - | CC6.1, CC6.7 | A.5.17, A.8.12 |
| No Pod Security Admission enforcement | 5.2.1 | CC6.8 | A.8.9 |
| No seccomp profile (RuntimeDefault) | 5.7.2 | CC6.8 | A.8.9 |
| hostPort used | 5.2.13 | CC6.6 | A.8.20 |
| Legacy ServiceAccount token Secrets | - | CC6.1 | A.5.17 |
| Non-admin RBAC can read Secrets | 5.1.2 | CC6.1, CC6.3 | A.8.2 |
| Non-admin RBAC can create pods | 5.1.4 | CC6.1, CC6.3 | A.8.2 |
| RBAC allows bind / escalate / impersonate | 5.1.8 | CC6.3 | A.8.2 |
| Admin UI or database exposed via LoadBalancer / NodePort | - | CC6.6 | A.8.20 |
| Cloud metadata endpoint reachable from pods | - | CC6.6 | A.8.20 |
| No PodDisruptionBudget on critical services | - | A1.2 | A.8.14 |
| Unsupported Kubernetes version | - | CC7.1 | A.8.8 |
| No API server audit policy | 3.2.1 | CC7.2 | A.8.15 |
| Audit logs not shipped off-cluster / no retention | - | CC7.2 | A.8.15 |
| Secrets not encrypted at rest with KMS | - (self-managed: the section 1.2 API server item for `--encryption-provider-config`; check the ID in the benchmark version you use) | CC6.1 | A.8.24 |
| Public API endpoint with no IP allowlist | - | CC6.6 | A.8.20 |
| Image vulnerabilities (Trivy HIGH/CRITICAL) | - | CC7.1 | A.8.8 |
