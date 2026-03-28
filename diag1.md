```mermaid
flowchart LR
    subgraph Source[Telemetry Sources]
    M(Prometheus Metrics) --> A(Alloy Receivers)
    L(Kubernetes Logs) --> A
    T(OTLP Traces) --> A
    end
    subgraph AlloyPipeline[Alloy Processing Pipeline]
    A --> Proc[Processors (e.g. relabel, filters)]
    Proc --> Exp[Exporters]
    end
    subgraph Dest[Backends]
    Exp --> Mimir[Grafana Mimir (Prometheus-Compatible)]
    Exp --> Loki[Grafana Loki (Logs)]
    Exp --> Tempo[Grafana Tempo (Traces)]
    Exp --> OTel[Other OTLP Backends]
    end
```
