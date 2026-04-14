from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .datalog_engine import DatalogEngine
from .model_loader import OSISemanticModel, get_behavior, load_osi_yaml


@dataclass
class Ontology:
    """
    Deterministic ontology query facade.

    This class loads an OSI YAML file and exposes a stable query API that can be used by
    higher-level agent orchestration systems.
    """

    version: str
    model: OSISemanticModel
    engine: DatalogEngine

    @classmethod
    def load(cls, path: str | Path, model_name: Optional[str] = None) -> "Ontology":
        version, models = load_osi_yaml(path)
        model = models[0]
        if model_name:
            found = next((m for m in models if m.name == model_name), None)
            if not found:
                raise ValueError(f"semantic_model '{model_name}' not found in file")
            model = found

        engine = DatalogEngine()
        cls._materialize(engine, model)
        return cls(version=version, model=model, engine=engine)

    # -------------------------
    # Materialization
    # -------------------------

    @staticmethod
    def _materialize(engine: DatalogEngine, model: OSISemanticModel) -> None:
        raw = model.raw

        # Datasets / fields
        for ds in raw.get("datasets") or []:
            if not isinstance(ds, dict) or "name" not in ds:
                continue
            ds_name = str(ds["name"])
            engine.add_dataset(ds_name)
            for f in ds.get("fields") or []:
                if not isinstance(f, dict) or "name" not in f:
                    continue
                engine.add_field(ds_name, str(f["name"]))

        # Relationships
        for rel in raw.get("relationships") or []:
            if not isinstance(rel, dict):
                continue
            try:
                rel_name = str(rel["name"])
                from_ds = str(rel["from"])
                to_ds = str(rel["to"])
                from_cols = [str(c) for c in rel.get("from_columns") or []]
                to_cols = [str(c) for c in rel.get("to_columns") or []]
            except Exception:
                continue
            if rel_name and from_ds and to_ds:
                engine.add_relationship(rel_name, from_ds, to_ds, from_cols, to_cols)

        # Metrics (names only for now; expression parsing is intentionally out of scope)
        for m in raw.get("metrics") or []:
            if not isinstance(m, dict) or "name" not in m:
                continue
            engine.add_metric(str(m["name"]))

        # Behavior: actions / rules / effects
        behavior = get_behavior(model)
        if isinstance(behavior, dict):
            actions = behavior.get("actions")
            if not isinstance(actions, list):
                actions = behavior.get("action_types") if isinstance(behavior.get("action_types"), list) else []

            for a in actions or []:
                if not isinstance(a, dict) or "id" not in a or "title" not in a:
                    continue
                action_id = str(a["id"])
                title = str(a["title"])
                kind = str(a.get("kind") or "")
                operation = str(a.get("operation") or "")
                engine.add_action(action_id, title, kind=kind, operation=operation)

                for eff in a.get("effects") or []:
                    if not isinstance(eff, dict):
                        continue
                    entity = str(eff.get("entity") or "")
                    mode = str(eff.get("mode") or "")
                    if not entity or not mode:
                        continue
                    selectors = eff.get("selectors") if isinstance(eff.get("selectors"), dict) else {}
                    dataset = str(selectors.get("dataset") or "")
                    field_names = selectors.get("field_names") or []
                    field = str(field_names[0]) if isinstance(field_names, list) and field_names else ""
                    impact_type = str(eff.get("impact_type") or "")
                    set_value = str(eff.get("set_value") or "")
                    transition = eff.get("transition") if isinstance(eff.get("transition"), dict) else {}
                    from_v = str(transition.get("from") or "")
                    to_v = str(transition.get("to") or "")
                    engine.add_effect(
                        action_id=action_id,
                        entity=entity,
                        mode=mode,
                        dataset=dataset,
                        field=field,
                        impact_type=impact_type,
                        set_value=set_value,
                        from_v=from_v,
                        to_v=to_v,
                    )

            for r in behavior.get("rules") or []:
                if not isinstance(r, dict) or "id" not in r or "title" not in r:
                    continue
                engine.add_rule(str(r["id"]), str(r["title"]), str(r.get("severity") or ""))

    # -------------------------
    # Deterministic query API
    # -------------------------

    def datasets(self) -> List[str]:
        return self.engine.list_datasets()

    def fields(self, dataset: str) -> List[str]:
        return self.engine.list_fields(dataset)

    def actions(self) -> List[str]:
        return self.engine.list_actions()

    def actions_affecting_field(self, dataset: str, field: str) -> List[str]:
        return self.engine.actions_affecting_field(dataset, field)

    def effects_of_action(self, action_id: str) -> List[Dict[str, Any]]:
        return self.engine.effects_of_action(action_id)

    def is_reachable(self, from_dataset: str, to_dataset: str) -> bool:
        return self.engine.reachable(from_dataset, to_dataset)

