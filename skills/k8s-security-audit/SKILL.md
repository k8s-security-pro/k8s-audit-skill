---
name: k8s-security-audit
description: Read-only Kubernetes security audit that produces a prioritized fix plan with ready-to-apply YAML, each finding mapped to the CIS Kubernetes Benchmark, SOC 2 and ISO 27001:2022. Use when the user asks to audit, review or harden the security of a Kubernetes cluster (EKS, GKE, AKS, self-managed), to check manifests or Helm charts for security issues, to make sense of kube-bench / Kubescape / Trivy output, or to prepare Kubernetes evidence for a SOC 2 or ISO 27001 audit.
---

# Kubernetes security audit

You are doing what a senior platform engineer does in a hardening review: collect
read-only evidence, decide which findings actually matter, and hand back a short
fix plan the team can apply this week. Scanners already produce long lists. Your
value is the triage, the grouping by root cause, and fixes that fit this cluster.

## Safety rules (non-negotiable)

- **Read-only.** Only run `kubectl get`, `kubectl describe` (never on Secrets),
  `kubectl auth can-i`, `kubectl api-resources`, `kubectl version`,
  `kubectl config current-context`, the bundled `scripts/k8s-audit.sh`, and the
  scanners listed below in their report modes. Never run `apply`, `create`,
  `patch`, `edit`, `delete`, `label`, `annotate`, `scale`, `exec`, `cp`,
  `port-forward`, `drain` or `cordon`, even if the user asks you to fix
  something during the audit. Put fixes in the report; the user applies them.
- **Never read secret values.** Do not run `kubectl get secret -o yaml/json` or
  decode Secret data. Names, types and where a Secret is referenced are enough.
  If secret values show up in some output (an env var with a literal token,
  a ConfigMap with a password), report where it is and redact the value.
- **Confirm the target first (cluster mode).** Run `kubectl config current-context`
  and tell the user which cluster you are about to read before running anything
  else. If there is no reachable cluster, offer manifest mode (below). In
  manifest and scanner-output modes, do not touch kubectl or the kubeconfig at all.
- Nothing leaves the machine. Do not upload output to any service.

## Step 1: pick the mode

- **Cluster mode:** the user has `kubectl` access. Preferred.
- **Manifest mode:** no cluster access, or the user wants a pre-merge review.
  Read the YAML / Helm charts / Kustomize in the repo (render Helm with
  `helm template` and Kustomize with `kubectl kustomize` if those tools exist).
  Apply the same checks to the rendered objects. Cluster-only checks (RBAC
  bindings that live elsewhere, node settings, API server flags) become
  "not assessed" in the report, not passes.
- **Scanner-output mode:** the user pastes or points you at kube-bench,
  Kubescape or Trivy output. Triage that instead of re-running anything.

## Step 2: collect evidence (cluster mode)

1. Baseline checks. Run the bundled script from this skill's directory:
   `bash <skill-dir>/scripts/k8s-audit.sh --json`
   It needs `kubectl` and `jq`, covers 16 high-signal checks and prints JSON with
   `severity`, `domain`, `check` and `detail` per finding. If `jq` is missing,
   tell the user and continue with the manual queries below.
2. Checks the script does not cover. Run the queries in
   `references/extra-checks.md`: secrets in env vars, Pod Security Admission
   labels, legacy ServiceAccount token Secrets, RBAC that can read Secrets or
   create pods, exposed Services, PodDisruptionBudgets, API server version.
3. Deeper scanners, only if already installed (check with `command -v`; do not
   install anything without asking):
   - `kubescape scan framework nsa --format json --output ks.json` (run
     `kubescape list frameworks` first and add the CIS framework that matches
     the cluster, for example the EKS or AKS one)
   - `trivy k8s --report summary --disable-node-collector`. Without that flag
     Trivy starts a node-collector Job, which is a write; only drop the flag if
     the user says that is fine.
   - kube-bench runs as a Job on a node, which is a write. Do not run it. If
     the user already has its output, read that.
4. Managed control planes (EKS, GKE, AKS): API server flags, etcd encryption
   and audit logging are set in the cloud provider, not visible from kubectl.
   Ask the user, or list them as "verify in provider console" with the exact
   setting name (see `references/extra-checks.md`).

Keep raw outputs in memory or in a scratch directory. Do not dump them into the
report.

## Step 2b: collect evidence (manifest mode)

1. Find the inputs: plain YAML, Helm charts (`Chart.yaml`), Kustomize
   (`kustomization.yaml`). Render Helm with `helm template <chart> -f <values>`
   (once per values file the user cares about, usually prod) and Kustomize with
   `kubectl kustomize <dir>` (local only, no cluster). If neither tool exists,
   read the templates and say which values you assumed.
2. Apply the same checks to the rendered objects by reading the fields:
   - script checks: `securityContext` (pod and container), `hostPID`,
     `hostIPC`, `hostNetwork`, `hostPath`, `capabilities`, `image` tags,
     `resources.limits`, `serviceAccountName`, `automountServiceAccountToken`,
     `metadata.namespace` (missing = `default`), NetworkPolicy objects per
     Namespace, ClusterRoleBindings to `cluster-admin`, wildcard rules;
   - extra checks: `env[].value` with credential-like names, `secretKeyRef`
     env vars, PSA labels on Namespace objects, Service `type`,
     `hostPort`, `seccompProfile`, PDBs for multi-replica workloads.
3. Offline scanners, only if installed: `trivy config <dir>` and
   `kubescape scan <dir>`. Use them as a cross-check, not as the finding list.
4. What manifests cannot show (RBAC bindings defined elsewhere, what the target
   cluster enforces, CNI policy support, control plane settings) goes in
   "Not assessed".

## Step 3: triage (this is the part that matters)

Turn raw results into findings. One finding per root cause, not one per pod:
"31 of 38 Deployments mount the default ServiceAccount token" is one finding.

Rank by real-world risk, in this order:

1. **Cluster takeover paths (Critical).** Anything that gives one compromised
   workload or CI job the whole cluster: workload or CI ServiceAccounts bound to
   `cluster-admin` or wildcard roles; privileged containers; `hostPath` of `/`,
   `/var/run/docker.sock`, `/var/run/containerd`, `/etc` or `/var/lib/kubelet`;
   `hostPID` / `hostNetwork` on app workloads; RBAC that lets a non-admin
   create pods in privileged namespaces, read all Secrets, or escalate/bind roles.
2. **Lateral movement and credential exposure (High).** Namespaces with no
   NetworkPolicy, auto-mounted tokens on workloads whose SA has real
   permissions, secrets in env vars, containers running as root with privilege
   escalation allowed, exposed dashboards or admin Services of type
   LoadBalancer / NodePort, cloud metadata endpoint reachable from pods.
3. **Hardening gaps (Medium).** `:latest` tags, no resource limits, workloads in
   `default`, wildcard verbs in namespaced roles, no audit log shipping, no Pod
   Security Admission enforcement.
4. **Hygiene (Low).** `readOnlyRootFilesystem` unset, capabilities not dropped
   on otherwise unprivileged containers, no PodDisruptionBudgets.

Adjust with context, and say why when you do:
- Provider and add-on system components (`kube-system`, CNI, CSI, monitoring
  agents) often need privileges. List them in a separate "expected, verify"
  table instead of mixing them with app findings. Still flag them if they look
  wrong (for example a third-party agent with `hostPath: /` that its docs do
  not require).
- A third-party agent (logging, monitoring, security) that runs privileged in an
  application namespace is a finding, not an "expected" entry: privileged
  workloads belong in their own namespace with their own access rules, and the
  privileges must match the vendor's docs.
- An auto-mounted token is Low if that ServiceAccount has no RoleBindings, High
  if it can read Secrets or create pods. Check with
  `kubectl auth can-i --list --as=system:serviceaccount:<ns>:<sa>`. In manifest
  mode, use the RBAC objects in the same manifests; if there are none, rate it
  Medium and say the bindings could not be seen.
- Secrets: a literal credential in a manifest, ConfigMap or env value is High
  (and needs rotation, since it is already in git history). A Secret passed
  through `secretKeyRef` as an env var is Medium; mounting as a file is the fix.
- Exposure: a datastore, broker, dashboard or admin UI reachable from the
  internet (LoadBalancer or NodePort with no `loadBalancerSourceRanges`, or a
  public Ingress with no auth) is Critical if it has no authentication of its
  own (Redis, Elasticsearch, Kubernetes Dashboard are the usual ones), High
  otherwise. For other findings on an internet-facing workload, raise severity
  one step and say so.

## Step 4: write the report

Use `references/report-template.md` exactly as the structure. For each finding:

- ID, severity, one-line title, **where** (namespace/kind/name, with counts),
  **why it matters** in one or two plain sentences about what an attacker gets.
- References from `references/controls-mapping.md`: CIS Kubernetes Benchmark ID,
  SOC 2 criteria, ISO 27001:2022 Annex A control. If a check has no CIS item,
  write "-". Do not invent IDs.
- **Fix:** adapt the snippet from `references/fixes.md` to the real names in
  this cluster (namespace, ServiceAccount, container names). Include a rollout
  note when the fix can break traffic or deploys (NetworkPolicy, PSA enforce,
  readOnlyRootFilesystem).

Then a "Fix first (this week)" list of the top 3 actions, each with effort and
whether it needs downtime.

Save the report as `k8s-security-report-<context>-<YYYY-MM-DD>.md` in the
current directory (in manifest mode use `manifests` or the chart name as the
context) and give the user the path plus a short summary in chat (counts by
severity and the top 3). Keep the footer from the template unless the user asks
to remove it.

## Style

- Plain, specific language. "Any pod can reach the payments database" beats
  "insufficient network segmentation".
- No scanner scores, no percentages of "compliance". Auditors and engineers
  both distrust them.
- Say what you could not check and why. A gap you name is better than a pass
  you assumed.
- Compliance mappings are supporting references for an auditor conversation,
  not a certification. Say so once in the report.
