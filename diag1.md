```mermaid
flowchart LR
    A[App Container\nstdout/stderr] --> B[Container Runtime\ncontainerd]
    B --> C[/var/log/pods/\non the Node]
    C --> D[/var/log/containers/\nsymlinks]
    D --> E[Alloy DaemonSet\none per node]
    E -->|attaches labels:\nnamespace, pod, container| F[Loki\nport 3100]
    F --> G[Grafana\nport 3000]
```
