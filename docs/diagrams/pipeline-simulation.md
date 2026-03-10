# Pipeline simulation flow

```mermaid
flowchart LR
  subgraph Config
    C1[Enable simulation]
    C2[Event density]
    C3[Pattern: steady / burst / seasonal / growth]
    C4[Replay: ordered / shuffled / windowed]
  end

  subgraph Generation
    G1[Table generation]
    G2[Event stream generation]
  end

  subgraph Output
    O1[Table exports: Parquet, CSV, ...]
    O2[Event stream JSONL]
  end

  C1 --> G1
  C2 --> G2
  C3 --> G2
  C4 --> G2
  G1 --> O1
  G2 --> O2
```

Pipeline simulation adds **event-stream** output alongside normal table data. Supported packs (e.g. ecommerce, fintech, logistics, IoT) define event types; the engine generates time-ordered events according to density and pattern. Replay mode affects how events are ordered in the output.
