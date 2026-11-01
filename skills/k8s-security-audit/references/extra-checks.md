# Extra checks (read-only)

Queries for findings the bundled script does not cover. All need `kubectl` and
`jq`. Add `-n <ns>` instead of `-A` to scope to one namespace. Skip
`kube-system` and other provider namespaces in the main findings; report them in
the "expected, verify" table.

## Secrets in environment variables (secretKeyRef)

```bash
kubectl get pods -A -o json | jq -r '
  .items[] | .metadata.namespace as $ns | .metadata.name as $p
  | .spec.containers[] | .name as $c
  | (.env // [])[] | select(.valueFrom.secretKeyRef)
  | "\($ns)/\($p) [\($c)] \(.name) <- secret \(.valueFrom.secretKeyRef.name)"' | sort -u
```

## Literal credentials in env (names only, never print values)

```bash
kubectl get pods -A -o json | jq -r '
  .items[] | .metadata.namespace as $ns | .metadata.name as $p
  | .spec.containers[] | (.env // [])[]
  | select(.value != null and (.name | test("PASS|SECRET|TOKEN|API_KEY|PRIVATE"; "i")))
  | "\($ns)/\($p) \(.name) (literal value, redacted)"' | sort -u
```

## Pod Security Admission labels per namespace

```bash
kubectl get ns -o json | jq -r '
  .items[] | [.metadata.name,
    (.metadata.labels["pod-security.kubernetes.io/enforce"] // "-"),
    (.metadata.labels["pod-security.kubernetes.io/warn"] // "-")] | @tsv'
```

Application namespaces with enforce `-` or `privileged` and no Kyverno /
Gatekeeper policy are a finding. Check for policy engines with
`kubectl get clusterpolicies.kyverno.io,constrainttemplates 2>/dev/null`.

## Legacy ServiceAccount token Secrets (long-lived tokens)

```bash
kubectl get secrets -A --field-selector type=kubernetes.io/service-account-token \
  -o custom-columns=NS:.metadata.namespace,NAME:.metadata.name,SA:.metadata.annotations.kubernetes\\.io/service-account\\.name
```

## RBAC: who can read Secrets, create pods, escalate

```bash
kubectl get clusterroles,roles -A -o json | jq -r '
  .items[] | select(.metadata.name | startswith("system:") | not)
  | . as $r | (.rules // [])[]
  | select(
      ((.resources // []) | any(. == "secrets" or . == "*")) and ((.verbs // []) | any(. == "get" or . == "list" or . == "watch" or . == "*"))
      or ((.resources // []) | any(. == "pods" or . == "*")) and ((.verbs // []) | any(. == "create" or . == "*"))
      or ((.verbs // []) | any(. == "bind" or . == "escalate" or . == "impersonate")))
  | "\($r.kind) \($r.metadata.namespace // "-")/\($r.metadata.name)"' | sort -u
```

Then find who holds those roles:

```bash
kubectl get clusterrolebindings,rolebindings -A -o json | jq -r '
  .items[] | select(.metadata.name | startswith("system:") | not)
  | "\(.kind) \(.metadata.namespace // "-")/\(.metadata.name): \(.roleRef.kind)/\(.roleRef.name) -> " +
  ([.subjects[]? | "\(.kind):\(.namespace // "")/\(.name)"] | join(", "))'
```

To see what one workload identity can actually do:
`kubectl auth can-i --list -n <ns> --as=system:serviceaccount:<ns>:<sa>`
(the `-n` matters: without it, namespaced Roles do not show up)

## Exposed Services

```bash
kubectl get svc -A -o json | jq -r '
  .items[] | select(.spec.type == "LoadBalancer" or .spec.type == "NodePort")
  | "\(.metadata.namespace)/\(.metadata.name) \(.spec.type) ports=\([.spec.ports[].port] | join(","))"'
```

Flag dashboards, databases, message brokers, metrics and admin UIs exposed this
way. Also list Ingress hosts: `kubectl get ingress -A`.

## Cloud metadata endpoint

Look for a NetworkPolicy (or CNI policy) that blocks egress to
`169.254.169.254/32`:

```bash
kubectl get networkpolicy -A -o json | jq -r '
  .items[] | select([.. | .except? // empty | .[]] | any(. == "169.254.169.254/32"))
  | "\(.metadata.namespace)/\(.metadata.name)"'
```

On EKS, IMDSv2 with hop limit 1 on nodes is the other valid control; ask the
user if it is set.

## PodDisruptionBudgets

```bash
kubectl get pdb -A
kubectl get deploy -A -o json | jq -r '.items[] | select(.spec.replicas > 1) | "\(.metadata.namespace)/\(.metadata.name)"'
```

Multi-replica Deployments with no matching PDB are a Low finding.

## Kubernetes version

`kubectl version -o json | jq -r .serverVersion.gitVersion`

Compare with the provider's supported versions (EKS, GKE, AKS each publish an
end-of-support calendar). Out of standard support is Medium.

## Managed control plane settings (ask the user or the console)

| Setting | EKS | GKE | AKS |
|---|---|---|---|
| API audit logs shipped | Control plane logging: audit enabled | Cloud Audit Logs (Admin Activity on by default, Data Access optional) | Diagnostic settings: kube-audit to Log Analytics |
| Secrets encryption with KMS | Envelope encryption with a KMS key | Application-layer secrets encryption | KMS etcd encryption |
| API endpoint exposure | Public access CIDRs or private endpoint | Authorized networks or private cluster | Authorized IP ranges or private cluster |
| Node metadata | IMDSv2 required, hop limit 1 | Workload Identity, metadata concealment | Workload Identity |
