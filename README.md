# ontology-query

A lightweight, deterministic ontology query engine for **OSI semantic models** (YAML). It loads a semantic model file, builds a small **knowledge graph**, materializes **Datalog facts**, and answers queries via a Python SDK or a CLI.

> This project is intentionally **not** a NL-to-SQL system. It focuses on **rigorous reasoning** over the ontology (datasets/fields/relationships/metrics/behavior).

## Features

- Load OSI YAML (`version`, `semantic_model`)
- Deterministic graph reasoning:
  - list datasets/fields/metrics/actions
  - find relationship paths between datasets
  - explain which actions can impact a field (via `effects`)
- Optional English NLQ adapter (rule-based) that maps a small set of question patterns to deterministic queries

## Install (local)

```bash
pip install -e . --break-system-packages
```

## Quickstart

```bash
ontq datasets --model examples/p2p_behavior_effects_minimal.yaml
ontq fields --model examples/p2p_behavior_effects_minimal.yaml --dataset suppliers
ontq actions-affecting --model examples/p2p_behavior_effects_minimal.yaml --dataset suppliers --field status
ontq join-path --model examples/p2p_behavior_effects_minimal.yaml --from suppliers --to suppliers
```

## English NLQ examples

```bash
ontq nlq --model examples/p2p_behavior_effects_minimal.yaml --question "Which actions can change suppliers.status?"
ontq nlq --model examples/p2p_behavior_effects_minimal.yaml --question "Show effects of suppliers/block"
```

## Python SDK

```python
from ontology_query import Ontology

onto = Ontology.load("examples/p2p_behavior_effects_minimal.yaml")
print(onto.datasets())
print(onto.fields("suppliers"))
print(onto.actions_affecting_field("suppliers", "status"))
```

## OSI behavior compatibility

This engine supports two ways to read behavior information:
- Preferred: `semantic_model[].behavior` (first-class)
- Legacy: `custom_extensions[].data` JSON blob containing behavior-layer fields (`action_types`, `rules`, ...)

## License

Apache-2.0

