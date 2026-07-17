flowchart TB
    subgraph Cluster["kind Cluster"]
        TA["Target App\n(Python HTTP Service)\n:8080"]
        CI["Chaos Injector\nscripts/chaos_inject.py"]
    end

    subgraph Observability["Observability Stack (docker compose)"]
        Prom["Prometheus\n:9090"]
        Loki["Loki\n:3100"]
        Temp["Tempo\n:4317"]
        Graf["Grafana :3000\nDashboards"]
        LF["Langfuse :3001\nLLM Traces"]
    end

    subgraph Agent["SRE Agent (FastAPI :8000)"]
        direction TB
        API["FastAPI Endpoints"]
        
        subgraph Pipeline["8-Stage Pipeline"]
            D1["1. detect"]
            D2["2. triage"]
            D3["3. diagnose"]
            D4["4. propose"]
            D5["5. approve"]
            D6["6. act"]
            D7["7. verify"]
            D8["8. close"]
        end

        subgraph Support["Supporting Services"]
            LLM["Ollama / Gemma 4\nor FakeSREModel"]
            RAG["ChromaDB\nRunbook Store"]
            GR["GuardRails AI\nPolicy Validator"]
            Audit["SQLite Audit Log"]
        end
    end

    subgraph UI["Demo UI"]
        ST["Streamlit Dashboard\nstreamlit_app.py"]
    end

    CI -- "POST /chaos/memory-leak" --> TA
    TA -- "/metrics scrape" --> Prom
    TA -- "logs" --> Loki
    TA -- "OTLP traces" --> Temp
    Prom -- "alert" --> API
    API --> Pipeline

    D2 -- "query metrics/logs/traces" --> Prom
    D2 -- "query logs" --> Loki
    D2 -- "query traces" --> Temp

    D3 -- "retrieve relevant runbook" --> RAG
    D3 --> LLM

    D4 -- "validate plan policy" --> GR
    D4 --> LLM

    D5 -- "human decision" --> ST

    D6 -- "kubectl (dry-run or exec)" --> TA

    D7 -- "check metric recovery" --> Prom

    D1 -.-> D2 -.-> D3 -.-> D4 -.-> D5 -.-> D6 -.-> D7 -.-> D8
    Pipeline -. "every transition logged" .-> Audit

    LLM -. "every LLM call traced" .-> LF
    Prom -. "system dashboards" .-> Graf
    Loki -. "log dashboards" .-> Graf
    Temp -. "trace dashboards" .-> Graf

    ST -- "HTTP" --> API
