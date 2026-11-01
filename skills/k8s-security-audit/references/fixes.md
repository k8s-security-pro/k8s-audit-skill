# Fix snippets

Starting points. Replace the example names (`payments`, `deployer`, `api`) with
the real ones from the cluster. Add a rollout note whenever a fix can block
traffic or deploys.

## cluster-admin bound to a workload or CI ServiceAccount

```yaml
# Replace cluster-admin with a namespaced Role per target namespace
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: deployer
  namespace: payments
rules:
- apiGroups: ["apps"]
  resources: ["deployments"]
  verbs: ["get", "list", "patch", "update"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: deployer
  namespace: payments
subjects:
- kind: ServiceAccount
  name: deployer
  namespace: ci
roleRef:
  kind: Role
  name: deployer
  apiGroup: rbac.authorization.k8s.io
```

Rollout: create the new Role and RoleBinding, run one pipeline, then delete the
ClusterRoleBinding.

## Wildcard verbs / resources in a Role

Replace `"*"` with the resources and verbs the subject actually uses. To find
them, check the API server audit log for that subject over a week, or start
from `kubectl auth can-i --list` and remove what is not needed.

## Privileged container, hostPath, host namespaces

```yaml
securityContext:
  privileged: false
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]
    # add: ["NET_BIND_SERVICE"]  # only what the app or vendor docs require
volumeMounts:
- name: proc
  mountPath: /host/proc
  readOnly: true
# remove hostPID / hostIPC / hostNetwork unless the agent's docs require them
```

Rollout: test on one node pool first for DaemonSets.

## Running as root, privilege escalation

```yaml
spec:
  securityContext:
    runAsNonRoot: true
    runAsUser: 10001
    fsGroup: 10001
    seccompProfile:
      type: RuntimeDefault
  containers:
  - name: api
    securityContext:
      allowPrivilegeEscalation: false
      capabilities:
        drop: ["ALL"]
```

Rollout: images that write to root-owned paths will fail; fix the Dockerfile
(`USER 10001`, chown the app dir) first.

## Pod Security Admission

```bash
# warn first, enforce once the warnings are gone
kubectl label ns payments \
  pod-security.kubernetes.io/warn=restricted \
  pod-security.kubernetes.io/enforce=baseline
```

## Namespace without NetworkPolicy

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: default-deny
  namespace: payments
spec:
  podSelector: {}
  policyTypes: ["Ingress", "Egress"]
---
# allow DNS, otherwise everything breaks after default-deny
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: allow-dns
  namespace: payments
spec:
  podSelector: {}
  policyTypes: ["Egress"]
  egress:
  - to:
    - namespaceSelector:
        matchLabels:
          kubernetes.io/metadata.name: kube-system
    ports:
    - { protocol: UDP, port: 53 }
    - { protocol: TCP, port: 53 }
```

Rollout: one namespace at a time, add allow rules for each real flow, watch for
blocked connections. Confirm the CNI enforces NetworkPolicy (the AWS VPC CNI
needs network policy support enabled; plain Flannel does not enforce, but k3s
ships its own NetworkPolicy controller alongside Flannel, so policies work there).

## Block cloud metadata endpoint

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-metadata
  namespace: payments
spec:
  podSelector: {}
  policyTypes: ["Egress"]
  egress:
  - to:
    - ipBlock:
        cidr: 0.0.0.0/0
        except: ["169.254.169.254/32"]
```

## Default ServiceAccount, auto-mounted tokens

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: default
  namespace: payments
automountServiceAccountToken: false
---
# workloads that do call the API get their own SA
apiVersion: v1
kind: ServiceAccount
metadata:
  name: api
  namespace: payments
automountServiceAccountToken: false   # set true on the pod spec only if needed
```

## Legacy ServiceAccount token Secrets

Delete them once nothing uses them; pods get short-lived projected tokens
automatically. If an external system needs a token, use
`kubectl create token <sa> --duration=1h` or workload identity instead.

## Secrets in env vars

```yaml
volumes:
- name: db-creds
  secret:
    secretName: payments-db
containers:
- name: api
  volumeMounts:
  - name: db-creds
    mountPath: /var/run/secrets/db
    readOnly: true
```

Literal credentials in env or ConfigMaps: move to a Secret (or External
Secrets Operator / CSI driver from the cloud secret manager) and rotate the
exposed value.

## :latest or untagged images

Pin to a version tag or digest (`image: registry/app@sha256:...`). Enforce with
a Kyverno or Gatekeeper policy so it does not come back.

## No resource limits

```yaml
resources:
  requests: { cpu: 100m, memory: 128Mi }
  limits:   { memory: 256Mi }
```

Plus a LimitRange per namespace so new workloads get defaults.

## Workloads in default namespace

Move each to its own namespace with its own RBAC, NetworkPolicy and PSA labels.

## No PodDisruptionBudget

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: api
  namespace: payments
spec:
  minAvailable: 1
  selector:
    matchLabels:
      app: api
```

## Exposed admin Service

Change to `ClusterIP` and reach it via `kubectl port-forward` or an
authenticated Ingress. For a LoadBalancer that must stay, restrict
`loadBalancerSourceRanges`.
