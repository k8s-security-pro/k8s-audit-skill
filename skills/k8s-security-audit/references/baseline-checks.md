# Baseline checks (read-only)

Sixteen high-signal checks in three `kubectl get` + `jq` commands. They read
Pod, Namespace, NetworkPolicy and RBAC objects only. They do not read Secret
objects, ConfigMaps or kubeconfig contents, and the output is limited to
namespace/name pairs and counts.

Run each block as one command. Add `-n <ns>` instead of `-A` to the first
command to scope pod checks to one namespace.

Each check prints one tab-separated line:

```
RESULT   CHECK   TITLE   COUNT   EXAMPLES (first 25)
```

`RESULT` is `PASS`, `WARN` or `FAIL`. The `#` numbers match the item numbers
in `controls-mapping.md` (k8s-security.pro 50-point checklist).

## 1. Workload checks (one read of all pods)

Results are per workload (`deploy/`, `daemonset/`, `statefulset/`, `job/`, or
`pod/` for bare pods), so replicas of one Deployment count once. Regular and
init containers are both checked.

```bash
kubectl get pods -A -o json | jq -r '
  def ctrs: (.spec.containers // []) + (.spec.initContainers // []);
  def workload:
    .metadata.namespace as $ns
    | (.metadata.labels["pod-template-hash"] // "") as $hash
    | ((.metadata.ownerReferences // [])[0]) as $o
    | if $o == null then "\($ns)/pod/\(.metadata.name)"
      elif $o.kind == "ReplicaSet" and $hash != "" then "\($ns)/deploy/\($o.name | rtrimstr("-" + $hash))"
      else "\($ns)/\($o.kind | ascii_downcase)/\($o.name)" end;
  def caps(f): (f // []) | map(ascii_upcase | ltrimstr("CAP_"));
  def row(sev; id; title; f):
    ([.items[] | select(f) | workload] | unique) as $h
    | [ (if ($h | length) == 0 then "PASS" else sev end), id, title,
        ($h | length | tostring),
        ($h[0:25] | join(", ")) + (if ($h | length) > 25 then ", +\(($h | length) - 25) more" else "" end)
      ] | @tsv;
  row("FAIL"; "#2"; "Privileged containers";
      any(ctrs[]; .securityContext.privileged == true)),
  row("FAIL"; "#3"; "allowPrivilegeEscalation not disabled";
      any(ctrs[]; .securityContext.allowPrivilegeEscalation != false)),
  row("WARN"; "#4"; "Running as root (runAsNonRoot unset)";
      (.spec.securityContext.runAsNonRoot != true)
      and all(ctrs[]; .securityContext.runAsNonRoot != true)),
  row("WARN"; "#4b"; "readOnlyRootFilesystem not set";
      any(ctrs[]; .securityContext.readOnlyRootFilesystem != true)),
  row("FAIL"; "#5"; "hostNetwork / hostPID / hostIPC";
      .spec.hostNetwork == true or .spec.hostPID == true or .spec.hostIPC == true),
  row("WARN"; "#6"; "ServiceAccount token mounted into the pod";
      any(.spec.volumes[]?; any(.projected.sources[]?; .serviceAccountToken != null))),
  row("WARN"; "#7"; "Capabilities not dropped (ALL)";
      any(ctrs[]; caps(.securityContext.capabilities.drop) | index("ALL") | not)),
  row("FAIL"; "#7b"; "Dangerous capabilities added";
      any(ctrs[]; caps(.securityContext.capabilities.add)
        | any(. == "SYS_ADMIN" or . == "NET_ADMIN" or . == "NET_RAW"
              or . == "SYS_PTRACE" or . == "SYS_MODULE" or . == "ALL"))),
  row("WARN"; "#9"; "hostPath volumes mounted";
      any(.spec.volumes[]?; .hostPath != null)),
  row("WARN"; "#15"; "Workloads using the default ServiceAccount";
      ((.spec.serviceAccountName // "default") == "default")
      and (.metadata.namespace | startswith("kube-") | not)),
  row("WARN"; "#20"; "Workloads in the default namespace";
      .metadata.namespace == "default"),
  row("WARN"; "#22"; "Containers without resource limits";
      any(ctrs[]; .resources.limits == null)),
  row("WARN"; "#28"; "Images using :latest or untagged";
      any(ctrs[]; .image as $i
        | ($i | test("@sha256:") | not)
          and (($i | test(":latest$")) or ($i | split("/") | last | test(":") | not))))
'
```

Notes:
- `#6` looks at what is actually mounted (the projected token volume Kubernetes
  adds), so it already accounts for `automountServiceAccountToken: false` on
  the pod or its ServiceAccount.
- A pod with `privileged: true` is also listed under `#3`; report it once,
  under privileged.
- When a count is above 25, rerun the same filter for that check alone if you
  need the full list.

## 2. Namespaces without a NetworkPolicy

```bash
kubectl get namespaces,networkpolicies -A -o json | jq -r '
  ([.items[] | select(.kind == "NetworkPolicy") | .metadata.namespace] | unique) as $np
  | [.items[] | select(.kind == "Namespace") | .metadata.name
     | select(test("^kube-(system|public|node-lease)$") | not)
     | select(. as $n | ($np | index($n)) == null)] as $miss
  | [ (if ($miss | length) == 0 then "PASS" else "FAIL" end), "#8",
      "Namespaces without a NetworkPolicy", ($miss | length | tostring),
      ($miss | join(", ")) ] | @tsv
'
```

A namespace that only has an allow-all policy passes this check but is still
open; look at the policies themselves when a namespace matters.

## 3. RBAC: cluster-admin bindings and wildcard roles

Built-in RBAC objects (label `kubernetes.io/bootstrapping=rbac-defaults`, such
as the `cluster-admin` ClusterRole and its binding to `system:masters`) and
`system:` roles are left out, so everything listed was added by someone.

```bash
kubectl get clusterrolebindings,clusterroles,roles -A -o json | jq -r '
  def builtin: (.metadata.labels["kubernetes.io/bootstrapping"] // "") == "rbac-defaults";
  [.items[] | select(.kind == "ClusterRoleBinding" and .roleRef.name == "cluster-admin")
   | select(builtin | not)
   | "\(.metadata.name) -> \([.subjects[]? | "\(.kind):\(.namespace // "")/\(.name)"] | join(" "))"] as $admins
  | [.items[] | select(.kind == "ClusterRole" or .kind == "Role")
     | select(((.metadata.name | startswith("system:")) or builtin) | not)
     | select(any(.rules[]?; ((.verbs // []) | index("*")) != null
                             and ((.resources // []) | index("*")) != null))
     | "\(.kind) \(.metadata.namespace // "-")/\(.metadata.name)"] as $wild
  | ([ (if ($admins | length) == 0 then "PASS" else "WARN" end), "#14",
       "Added cluster-admin bindings", ($admins | length | tostring), ($admins | join("; ")) ] | @tsv),
    ([ (if ($wild | length) == 0 then "PASS" else "WARN" end), "#16",
       "Roles granting * verbs on * resources", ($wild | length | tostring), ($wild[0:25] | join(", ")) ] | @tsv)
'
```

Managed providers and add-ons sometimes bind their own components to
cluster-admin; list those under "expected, verify". A binding to a workload or
CI ServiceAccount, or to a human user or group, is a finding.

## After the baseline

Continue with `extra-checks.md` for what these three commands do not cover.
For deeper CIS and NSA coverage, the deep run adds Kubescape and Trivy.

The same checks are also published as a standalone CI tool for use without
Claude: https://github.com/k8s-security-pro/k8s-audit
