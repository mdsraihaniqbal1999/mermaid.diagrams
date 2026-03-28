```mermaid
flowchart LR
    A[App Container<br>stdout/stderr] --> B[Container Runtime<br>containerd]
    B --> C[/var/log/pods/<br>on the Node]
    C --> D[/var/log/containers/<br>symlinks]
    D --> E[Alloy DaemonSet<br>one per node]
    E -->|attaches labels:<br>namespace, pod, container| F[Loki<br>port 3100]
    F --> G[Grafana<br>port 3000]
```
