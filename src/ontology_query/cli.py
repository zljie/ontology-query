import argparse
import json
from typing import Any

from .nlq import EnglishNLQ
from .ontology import Ontology


def _print(obj: Any, as_json: bool) -> None:
    if as_json:
        print(json.dumps(obj, ensure_ascii=False, indent=2))
    else:
        if isinstance(obj, list):
            for x in obj:
                print(x)
        else:
            print(obj)


def main() -> None:
    parser = argparse.ArgumentParser(prog="ontq", description="Deterministic ontology query tool for OSI YAML models.")
    parser.add_argument("--model", required=True, help="Path to OSI YAML semantic model")
    parser.add_argument("--model-name", default=None, help="Optional semantic_model.name to select")
    parser.add_argument("--json", action="store_true", help="Print JSON output")

    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("datasets", help="List datasets")

    p_fields = sub.add_parser("fields", help="List fields of a dataset")
    p_fields.add_argument("--dataset", required=True)

    p_actions = sub.add_parser("actions", help="List actions")

    p_aff = sub.add_parser("actions-affecting", help="List actions affecting a dataset.field")
    p_aff.add_argument("--dataset", required=True)
    p_aff.add_argument("--field", required=True)

    p_eff = sub.add_parser("effects", help="Show effects of an action")
    p_eff.add_argument("--action", required=True)

    p_reach = sub.add_parser("reachable", help="Check dataset reachability via relationships (transitive)")
    p_reach.add_argument("--from", dest="from_ds", required=True)
    p_reach.add_argument("--to", dest="to_ds", required=True)

    p_nlq = sub.add_parser("nlq", help="Ask a supported English question (rule-based)")
    p_nlq.add_argument("--question", required=True)

    args = parser.parse_args()
    onto = Ontology.load(args.model, model_name=args.model_name)

    if args.cmd == "datasets":
        _print(onto.datasets(), args.json)
        return

    if args.cmd == "fields":
        _print(onto.fields(args.dataset), args.json)
        return

    if args.cmd == "actions":
        _print(onto.actions(), args.json)
        return

    if args.cmd == "actions-affecting":
        _print(onto.actions_affecting_field(args.dataset, args.field), args.json)
        return

    if args.cmd == "effects":
        _print(onto.effects_of_action(args.action), args.json)
        return

    if args.cmd == "reachable":
        _print({"reachable": onto.is_reachable(args.from_ds, args.to_ds)}, args.json or True)
        return

    if args.cmd == "nlq":
        adapter = EnglishNLQ()
        res = adapter.ask(onto, args.question)
        _print({"intent": res.intent, "args": res.args, "result": res.result}, True)
        return


if __name__ == "__main__":
    main()

