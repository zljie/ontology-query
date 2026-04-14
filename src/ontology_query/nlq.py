import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .ontology import Ontology


@dataclass(frozen=True)
class NLQResult:
    intent: str
    args: Dict[str, Any]
    result: Any


class EnglishNLQ:
    """
    A minimal, rule-based English NLQ adapter.

    This is intentionally conservative: it only supports a small set of question patterns
    and always maps to deterministic ontology queries.
    """

    _re_actions_affecting = re.compile(
        r"^(which|what)\s+actions\s+can\s+(change|update|modify)\s+([a-zA-Z0-9_]+)\.([a-zA-Z0-9_]+)\??$",
        re.IGNORECASE,
    )
    _re_show_effects = re.compile(r"^(show|list)\s+effects\s+of\s+([a-zA-Z0-9_\-/]+)\??$", re.IGNORECASE)
    _re_list_datasets = re.compile(r"^(list|show)\s+datasets\??$", re.IGNORECASE)
    _re_list_fields = re.compile(r"^(list|show)\s+fields\s+of\s+([a-zA-Z0-9_]+)\??$", re.IGNORECASE)

    def ask(self, onto: Ontology, question: str) -> NLQResult:
        q = question.strip()

        m = self._re_list_datasets.match(q)
        if m:
            res = onto.datasets()
            return NLQResult(intent="datasets", args={}, result=res)

        m = self._re_list_fields.match(q)
        if m:
            dataset = m.group(2)
            res = onto.fields(dataset)
            return NLQResult(intent="fields", args={"dataset": dataset}, result=res)

        m = self._re_actions_affecting.match(q)
        if m:
            dataset = m.group(3)
            field = m.group(4)
            res = onto.actions_affecting_field(dataset, field)
            return NLQResult(intent="actions_affecting_field", args={"dataset": dataset, "field": field}, result=res)

        m = self._re_show_effects.match(q)
        if m:
            action_id = m.group(2)
            res = onto.effects_of_action(action_id)
            return NLQResult(intent="effects_of_action", args={"action_id": action_id}, result=res)

        raise ValueError(
            "Unsupported question. Try: "
            "'List datasets', "
            "'List fields of <dataset>', "
            "'Which actions can change <dataset>.<field>?', "
            "'Show effects of <action_id>'"
        )

