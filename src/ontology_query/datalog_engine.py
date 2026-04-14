from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Tuple

from pyDatalog import pyDatalog


@dataclass(frozen=True)
class JoinEdge:
    rel_name: str
    from_ds: str
    to_ds: str
    from_cols: Tuple[str, ...]
    to_cols: Tuple[str, ...]


# NOTE: pyDatalog.create_terms defines symbols in the module global namespace.
# It must run at import time (not inside a class body) to avoid NameError.
pyDatalog.create_terms(
    "Dataset, Field, Relationship, Metric, Action, Effect, Rule, "
    "RelEdge, RelStep, Reachable, "
    "Ds, F, From, To, R, A, E, M, "
    "RelName, FC, TC, Kind, Op, Entity, Mode, ImpactType, SetValue, FromV, ToV, "
    "AffectsField"
)


class DatalogEngine:
    """
    A minimal Datalog knowledge base for OSI semantic models.

    The goal is deterministic inference, not probabilistic matching.
    """

    def __init__(self) -> None:
        pyDatalog.clear()

        # Derived predicates
        # Reachable(From, To) - transitive closure over relationship edges.
        Reachable(From, To) <= Relationship(RelName, From, To)
        Reachable(From, To) <= Relationship(RelName, From, Ds) & Reachable(Ds, To)

        # actions that affect a dataset.field
        # Effect fields are stored as: Effect(A, Entity, Mode, Ds, F, ImpactType, SetValue, FromV, ToV)
        AffectsField(A, Ds, F) <= Effect(A, "field", Mode, Ds, F, ImpactType, SetValue, FromV, ToV) & (Mode == "write")

    # -------------------------
    # Assertion helpers
    # -------------------------

    def add_dataset(self, name: str) -> None:
        pyDatalog.assert_fact("Dataset", name)

    def add_field(self, dataset: str, field: str) -> None:
        pyDatalog.assert_fact("Field", dataset, field)

    def add_relationship(self, rel_name: str, from_ds: str, to_ds: str, from_cols: Iterable[str], to_cols: Iterable[str]) -> None:
        pyDatalog.assert_fact("Relationship", rel_name, from_ds, to_ds)
        # Persist columns as joined string to keep facts simple (still deterministic).
        pyDatalog.assert_fact("RelEdge", rel_name, from_ds, to_ds, ",".join(from_cols), ",".join(to_cols))

    def add_metric(self, name: str) -> None:
        pyDatalog.assert_fact("Metric", name)

    def add_action(self, action_id: str, title: str, kind: Optional[str] = None, operation: Optional[str] = None) -> None:
        pyDatalog.assert_fact("Action", action_id, title, kind or "", operation or "")

    def add_effect(
        self,
        action_id: str,
        entity: str,
        mode: str,
        dataset: str = "",
        field: str = "",
        impact_type: str = "",
        set_value: str = "",
        from_v: str = "",
        to_v: str = "",
    ) -> None:
        pyDatalog.assert_fact("Effect", action_id, entity, mode, dataset, field, impact_type, set_value, from_v, to_v)

    def add_rule(self, rule_id: str, title: str, severity: str) -> None:
        pyDatalog.assert_fact("Rule", rule_id, title, severity)

    # -------------------------
    # Query API
    # -------------------------

    def list_datasets(self) -> List[str]:
        q = pyDatalog.ask("Dataset(Ds)")
        return sorted({ans[0] for ans in (q.answers or [])})

    def list_fields(self, dataset: str) -> List[str]:
        q = pyDatalog.ask(f"Field('{dataset}', F)")
        return sorted({ans[0] for ans in (q.answers or [])})

    def reachable(self, from_ds: str, to_ds: str) -> bool:
        q = pyDatalog.ask(f"Reachable('{from_ds}','{to_ds}')")
        return bool(q and q.answers)

    def list_actions(self) -> List[str]:
        q = pyDatalog.ask("Action(A, R, Kind, Op)")
        return sorted({ans[0] for ans in (q.answers or [])})

    def actions_affecting_field(self, dataset: str, field: str) -> List[str]:
        q = pyDatalog.ask(f"AffectsField(A, '{dataset}', '{field}')")
        return sorted({ans[0] for ans in (q.answers or [])})

    def effects_of_action(self, action_id: str) -> List[Dict[str, Any]]:
        q = pyDatalog.ask(f"Effect('{action_id}', Entity, Mode, Ds, F, ImpactType, SetValue, FromV, ToV)")
        out: List[Dict[str, Any]] = []
        for (entity, mode, ds, f, impact_type, set_value, from_v, to_v) in (q.answers or []):
            out.append(
                {
                    "entity": entity,
                    "mode": mode,
                    "dataset": ds,
                    "field": f,
                    "impact_type": impact_type,
                    "set_value": set_value,
                    "transition": {"from": from_v, "to": to_v} if from_v or to_v else None,
                }
            )
        return out
