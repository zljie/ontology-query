import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


@dataclass(frozen=True)
class OSISemanticModel:
    """A minimal in-memory view of a single semantic_model entry."""

    name: str
    raw: Dict[str, Any]


def _parse_custom_extension_data(ext: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Parse OSI custom_extensions.data which is a JSON string."""
    data = ext.get("data")
    if not isinstance(data, str) or not data.strip():
        return None
    try:
        return json.loads(data)
    except Exception:
        return None


def _extract_legacy_behavior_from_extensions(custom_extensions: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Best-effort extraction for legacy behavior layer embedded in custom_extensions.

    NOTE: OSI core-spec encodes vendor-specific extension content as a JSON string, so this is necessarily
    heuristic. We simply look for keys that resemble behavior-layer objects.
    """
    for ext in custom_extensions or []:
        data = _parse_custom_extension_data(ext)
        if not isinstance(data, dict):
            continue
        if "namespace" in data and "behavior_layer_version" in data and ("action_types" in data or "actions" in data):
            return data
    return None


def load_osi_yaml(path: str | Path) -> Tuple[str, List[OSISemanticModel]]:
    """
    Load an OSI YAML file (core spec) and return (version, semantic_models).
    """
    p = Path(path)
    payload = yaml.safe_load(p.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("Invalid OSI YAML: root must be an object")

    version = payload.get("version")
    if not isinstance(version, str):
        raise ValueError("Invalid OSI YAML: missing string 'version'")

    semantic_model = payload.get("semantic_model")
    if not isinstance(semantic_model, list) or not semantic_model:
        raise ValueError("Invalid OSI YAML: missing non-empty 'semantic_model' array")

    models: List[OSISemanticModel] = []
    for entry in semantic_model:
        if not isinstance(entry, dict) or "name" not in entry:
            continue
        models.append(OSISemanticModel(name=str(entry["name"]), raw=entry))

    if not models:
        raise ValueError("Invalid OSI YAML: no valid semantic_model entries")
    return version, models


def get_behavior(model: OSISemanticModel) -> Optional[Dict[str, Any]]:
    """
    Return behavior object from:
    1) semantic_model.behavior (preferred)
    2) custom_extensions embedded behavior (legacy)
    """
    raw = model.raw

    behavior = raw.get("behavior")
    if isinstance(behavior, dict):
        return behavior

    # legacy: custom_extensions is semantic_model-level in core spec, but some producers may also embed under dataset.
    ce = raw.get("custom_extensions")
    if isinstance(ce, list):
        legacy = _extract_legacy_behavior_from_extensions(ce)
        if legacy:
            return legacy

    datasets = raw.get("datasets") or []
    if isinstance(datasets, list):
        for ds in datasets:
            if not isinstance(ds, dict):
                continue
            ds_ce = ds.get("custom_extensions")
            if isinstance(ds_ce, list):
                legacy = _extract_legacy_behavior_from_extensions(ds_ce)
                if legacy:
                    return legacy
    return None

