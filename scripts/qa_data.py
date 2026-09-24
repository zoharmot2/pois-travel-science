#!/usr/bin/env python3
"""Validate generated website data before publication.

The validator is intentionally dependency-free so it can run locally and in
GitHub Actions. It treats ArcGIS exports as authoritative source data and
reports website-facing integrity problems without rewriting source records.

Exit codes:
    0: PASS or WARN
    1: one or more ERROR issues (or warnings with --fail-on-warnings)
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$",
    re.IGNORECASE,
)

GEOMETRY_FAMILIES = {
    "Point": "point",
    "MultiPoint": "point",
    "LineString": "line",
    "MultiLineString": "line",
    "Polygon": "polygon",
    "MultiPolygon": "polygon",
}

REMOTE_SCHEMES = {"http", "https"}
SUSPICIOUS_PLACEHOLDERS = {"undefined", "null", "none", "n/a", "na"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_uuid(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip().lower()
    if text.startswith("{") and text.endswith("}"):
        text = text[1:-1].strip()
    return text if UUID_RE.fullmatch(text) else None


def read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def nested_numbers(value: Any) -> Iterable[float]:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        yield float(value)
    elif isinstance(value, list):
        for child in value:
            yield from nested_numbers(child)


def iter_positions(coords: Any) -> Iterable[tuple[float, float]]:
    """Yield coordinate pairs from any supported GeoJSON coordinate nesting."""
    if not isinstance(coords, list) or not coords:
        return
    if (
        len(coords) >= 2
        and isinstance(coords[0], (int, float))
        and isinstance(coords[1], (int, float))
        and not isinstance(coords[0], bool)
        and not isinstance(coords[1], bool)
    ):
        yield float(coords[0]), float(coords[1])
        return
    for child in coords:
        yield from iter_positions(child)


def validate_geometry(geometry: Any) -> tuple[str | None, str | None]:
    """Return (family, error_message). Topological validation is out of scope."""
    if not isinstance(geometry, dict):
        return None, "Geometry is missing or is not an object."

    geometry_type = geometry.get("type")
    family = GEOMETRY_FAMILIES.get(geometry_type)
    if family is None:
        return None, f"Unsupported geometry type: {geometry_type!r}."

    coords = geometry.get("coordinates")
    positions = list(iter_positions(coords))
    if not positions:
        return family, "Geometry has no usable coordinate positions."

    for lon, lat in positions:
        if not math.isfinite(lon) or not math.isfinite(lat):
            return family, "Geometry contains a non-finite coordinate."
        if not (-180 <= lon <= 180 and -90 <= lat <= 90):
            return family, f"Coordinate outside WGS84 longitude/latitude range: [{lon}, {lat}]."

    return family, None


def safe_repo_path(repo_root: Path, reference: str) -> tuple[Path | None, str | None]:
    path = Path(reference.replace("\\", "/"))
    if path.is_absolute():
        return None, "Attachment path is absolute."
    resolved = (repo_root / path).resolve()
    try:
        resolved.relative_to(repo_root.resolve())
    except ValueError:
        return None, "Attachment path escapes the repository root."
    return resolved, None


class QaReport:
    def __init__(self, repo_root: Path, config_path: Path):
        self.repo_root = repo_root
        self.config_path = config_path
        self.issues: list[dict[str, Any]] = []
        self.datasets: list[dict[str, Any]] = []
        self.summary: dict[str, Any] = {
            "datasetCount": 0,
            "activeDatasetCount": 0,
            "entityCount": 0,
            "stableIdCount": 0,
            "attachmentReferenceCount": 0,
            "localAttachmentCount": 0,
            "remoteAttachmentCount": 0,
            "missingAttachmentCount": 0,
            "orphanAttachmentCount": 0,
            "mediaMetadataCount": 0,
            "warningCount": 0,
            "errorCount": 0,
        }
        self.counts = {
            "geometryFamilies": Counter(),
            "topics": Counter(),
            "types": Counter(),
            "mediaKinds": Counter(),
            "mediaStorage": Counter(),
        }
        self.deltas: dict[str, Any] | None = None
        self.layer_metadata: dict[str, Any] | None = None
        self.domain_comparison: dict[str, Any] = {}

    def add_issue(
        self,
        severity: str,
        code: str,
        message: str,
        *,
        dataset: str | None = None,
        count: int | None = None,
        examples: list[Any] | None = None,
    ) -> None:
        severity = severity.upper()
        issue: dict[str, Any] = {
            "severity": severity,
            "code": code,
            "message": message,
        }
        if dataset is not None:
            issue["dataset"] = dataset
        if count is not None:
            issue["count"] = count
        if examples:
            issue["examples"] = examples[:10]
        self.issues.append(issue)
        if severity == "ERROR":
            self.summary["errorCount"] += 1
        elif severity == "WARNING":
            self.summary["warningCount"] += 1

    @property
    def status(self) -> str:
        if self.summary["errorCount"]:
            return "ERROR"
        if self.summary["warningCount"]:
            return "WARNING"
        return "PASS"

    def as_dict(self) -> dict[str, Any]:
        result = {
            "schemaVersion": 1,
            "generatedAt": utc_now(),
            "status": self.status,
            "repositoryRoot": ".",
            "config": str(self.config_path.relative_to(self.repo_root)).replace("\\", "/"),
            "summary": self.summary,
            "counts": {
                "geometryFamilies": dict(sorted(self.counts["geometryFamilies"].items())),
                "topics": dict(sorted(self.counts["topics"].items())),
                "types": dict(sorted(self.counts["types"].items())),
                "mediaKinds": dict(sorted(self.counts["mediaKinds"].items())),
                "mediaStorage": dict(sorted(self.counts["mediaStorage"].items())),
            },
            "datasets": self.datasets,
            "issues": self.issues,
        }
        if self.deltas is not None:
            result["changesFromBaseline"] = self.deltas
        if self.layer_metadata is not None:
            result["layerMetadataValidation"] = self.layer_metadata
        if self.domain_comparison:
            result["domainComparison"] = self.domain_comparison
        return result


def load_configured_types(repo_root: Path, config: dict[str, Any], report: QaReport) -> set[str]:
    rel = config.get("symbologyConfigPath", config.get("topicConfigPath", "config.json"))
    path = repo_root / rel
    if not path.exists():
        report.add_issue("ERROR", "SYMBOL_CONFIG_MISSING", f"Symbology configuration file is missing: {rel}")
        return set()
    try:
        site_config = read_json(path)
    except Exception as exc:
        report.add_issue("ERROR", "SYMBOL_CONFIG_INVALID", f"Cannot parse {rel}: {exc}")
        return set()

    symbology = site_config.get("symbology", {})
    configured_field = symbology.get("field")
    expected_field = config.get("typeField", "POI_Type")
    if configured_field != expected_field:
        report.add_issue(
            "ERROR",
            "SYMBOL_FIELD_MISMATCH",
            f"config.json symbology.field is {configured_field!r}, expected {expected_field!r}.",
        )

    types = symbology.get("types", {})
    if not isinstance(types, dict):
        report.add_issue("ERROR", "TYPE_CONFIG_INVALID", "config.json symbology.types must be an object.")
        return set()
    return {str(key) for key in types}


def load_dataset(path: Path) -> tuple[list[dict[str, Any]] | None, str | None]:
    try:
        data = read_json(path)
    except Exception as exc:
        return None, f"Cannot parse GeoJSON: {exc}"
    if not isinstance(data, dict) or data.get("type") != "FeatureCollection":
        return None, "GeoJSON root must be a FeatureCollection."
    features = data.get("features")
    if not isinstance(features, list):
        return None, "GeoJSON FeatureCollection.features must be an array."
    return features, None


def validate_sidecar(
    repo_root: Path,
    rel_path: str,
    valid_entity_ids: set[str],
    report: QaReport,
) -> None:
    path = repo_root / rel_path
    if not path.exists():
        report.add_issue("WARNING", "SIDECAR_MISSING", f"Website metadata sidecar is missing: {rel_path}")
        return
    try:
        data = read_json(path)
    except Exception as exc:
        report.add_issue("ERROR", "SIDECAR_INVALID_JSON", f"Cannot parse {rel_path}: {exc}")
        return
    if not isinstance(data, dict):
        report.add_issue("ERROR", "SIDECAR_INVALID", "Metadata sidecar root must be an object.")
        return
    if data.get("schemaVersion") != 1:
        report.add_issue(
            "ERROR",
            "SIDECAR_SCHEMA_UNSUPPORTED",
            f"Metadata sidecar schemaVersion must be 1, found {data.get('schemaVersion')!r}.",
        )
    entities = data.get("entities")
    if not isinstance(entities, dict):
        report.add_issue("ERROR", "SIDECAR_INVALID", "Metadata sidecar entities must be an object.")
        return

    invalid_keys: list[str] = []
    orphan_ids: list[str] = []
    normalized_seen: set[str] = set()
    duplicate_ids: list[str] = []
    invalid_records: list[str] = []

    for raw_id, metadata in entities.items():
        normalized = normalize_uuid(raw_id)
        if normalized is None:
            invalid_keys.append(str(raw_id))
            continue
        if normalized in normalized_seen:
            duplicate_ids.append(normalized)
        normalized_seen.add(normalized)
        if normalized not in valid_entity_ids:
            orphan_ids.append(normalized)
        if not isinstance(metadata, dict):
            invalid_records.append(normalized)

    if invalid_keys:
        report.add_issue(
            "ERROR", "SIDECAR_INVALID_ID", "Metadata sidecar contains invalid entity IDs.",
            count=len(invalid_keys), examples=invalid_keys,
        )
    if duplicate_ids:
        report.add_issue(
            "ERROR", "SIDECAR_DUPLICATE_ID", "Metadata sidecar contains IDs that normalize to duplicates.",
            count=len(duplicate_ids), examples=duplicate_ids,
        )
    if invalid_records:
        report.add_issue(
            "ERROR", "SIDECAR_INVALID_RECORD", "Metadata sidecar entity records must be objects.",
            count=len(invalid_records), examples=invalid_records,
        )
    if orphan_ids:
        report.add_issue(
            "WARNING", "SIDECAR_ORPHAN_ID",
            "Metadata sidecar references entities that are not present in the current exported datasets.",
            count=len(orphan_ids), examples=orphan_ids,
        )


def feature_stable_ids(features: list[dict[str, Any]], field: str) -> set[str]:
    ids: set[str] = set()
    for feature in features:
        props = feature.get("properties") if isinstance(feature, dict) else None
        if not isinstance(props, dict):
            continue
        normalized = normalize_uuid(props.get(field))
        if normalized:
            ids.add(normalized)
    return ids


def compare_baseline(
    repo_root: Path,
    baseline_root: Path,
    dataset_specs: list[dict[str, Any]],
    stable_id_field: str,
    current_ids_by_dataset: dict[str, set[str]],
    report: QaReport,
) -> None:
    per_dataset: dict[str, Any] = {}
    total_added: set[tuple[str, str]] = set()
    total_removed: set[tuple[str, str]] = set()

    for spec in dataset_specs:
        name = str(spec.get("name"))
        rel = Path(str(spec.get("path")))
        baseline_path = baseline_root / rel
        if not baseline_path.exists():
            per_dataset[name] = {"status": "baseline-not-present", "added": None, "removed": None}
            continue
        features, error = load_dataset(baseline_path)
        if error or features is None:
            per_dataset[name] = {"status": "baseline-invalid", "added": None, "removed": None, "message": error}
            continue
        old_ids = feature_stable_ids(features, stable_id_field)
        new_ids = current_ids_by_dataset.get(name, set())
        added = sorted(new_ids - old_ids)
        removed = sorted(old_ids - new_ids)
        per_dataset[name] = {
            "status": "compared",
            "added": len(added),
            "removed": len(removed),
            "addedExamples": added[:10],
            "removedExamples": removed[:10],
        }
        total_added.update((name, value) for value in added)
        total_removed.update((name, value) for value in removed)

    report.deltas = {
        "baselineRoot": str(baseline_root),
        "added": len(total_added),
        "removed": len(total_removed),
        "datasets": per_dataset,
    }



def normalize_domain_values(entries: Any) -> tuple[set[str], list[Any], list[str]]:
    """Return (codes, invalid_entries, duplicate_codes) for ArcGIS coded values."""
    if not isinstance(entries, list):
        return set(), [entries], []
    codes: set[str] = set()
    invalid: list[Any] = []
    duplicates: list[str] = []
    for entry in entries:
        if not isinstance(entry, dict) or entry.get("code") is None:
            invalid.append(entry)
            continue
        code = str(entry.get("code")).strip()
        if not code:
            invalid.append(entry)
            continue
        if code in codes:
            duplicates.append(code)
        codes.add(code)
    return codes, invalid, duplicates


def actual_observed_values(features: list[dict[str, Any]], field_name: str) -> set[str]:
    values: set[str] = set()
    for feature in features:
        if not isinstance(feature, dict):
            continue
        props = feature.get("properties")
        if not isinstance(props, dict):
            continue
        value = props.get(field_name)
        if value is None:
            continue
        text = str(value).strip()
        if text and text.lower() not in {"none", "null"}:
            values.add(text)
    return values


def actual_attachment_summary(
    features: list[dict[str, Any]],
    attachment_field: str,
    attachment_media_field: str,
) -> dict[str, Any]:
    summary = {
        "references": 0,
        "local": 0,
        "remote": 0,
        "byKind": {"image": 0, "audio": 0, "video": 0, "other": 0},
    }
    for feature in features:
        if not isinstance(feature, dict):
            continue
        props = feature.get("properties")
        if not isinstance(props, dict):
            continue
        media = props.get(attachment_media_field, [])
        if isinstance(media, list):
            for item in media:
                if not isinstance(item, dict):
                    continue
                summary["references"] += 1
                storage = item.get("storage")
                if storage in ("local", "remote"):
                    summary[storage] += 1
                kind = item.get("kind")
                if kind in summary["byKind"]:
                    summary["byKind"][kind] += 1
                else:
                    summary["byKind"]["other"] += 1
        elif isinstance(props.get(attachment_field), list):
            # The Stage 10 contract should always have structured media metadata.
            # Keep the reference count useful even if the dedicated QA check reports
            # the missing/invalid metadata elsewhere.
            summary["references"] += len([
                ref for ref in props.get(attachment_field, [])
                if isinstance(ref, str) and ref.strip()
            ])
    return summary


def validate_layers_metadata(
    repo_root: Path,
    config: dict[str, Any],
    specs: list[dict[str, Any]],
    attachment_field: str,
    attachment_media_field: str,
    report: QaReport,
) -> None:
    """Cross-check harvested ArcGIS layer metadata against exported GeoJSON.

    Domain divergence between layers is allowed. The report records alignment and
    union values, while only malformed metadata or actual export/metadata
    inconsistencies are treated as errors.
    """
    rel_path = config.get("layersMetadataPath", "data/derived/layers-metadata.json")
    path = repo_root / rel_path
    if not path.exists():
        report.add_issue("ERROR", "LAYER_METADATA_MISSING", f"Layer metadata file is missing: {rel_path}")
        return
    try:
        root = read_json(path)
    except Exception as exc:
        report.add_issue("ERROR", "LAYER_METADATA_INVALID_JSON", f"Cannot parse {rel_path}: {exc}")
        return
    if not isinstance(root, dict):
        report.add_issue("ERROR", "LAYER_METADATA_INVALID", "Layer metadata root must be an object.")
        return
    if root.get("schemaVersion") != 1:
        report.add_issue(
            "ERROR",
            "LAYER_METADATA_SCHEMA_UNSUPPORTED",
            f"layers-metadata.json schemaVersion must be 1, found {root.get('schemaVersion')!r}.",
        )

    expected_server = str(config.get("expectedFeatureServerUrl") or "").rstrip("/")
    actual_server = str(root.get("featureServerUrl") or "").rstrip("/")
    if expected_server and actual_server != expected_server:
        report.add_issue(
            "ERROR",
            "FEATURE_SERVER_URL_MISMATCH",
            "Layer metadata was generated from an unexpected ArcGIS FeatureServer URL.",
            examples=[{"expected": expected_server, "actual": actual_server}],
        )

    metadata_datasets = root.get("datasets")
    if not isinstance(metadata_datasets, dict):
        report.add_issue("ERROR", "LAYER_METADATA_INVALID", "layers-metadata.json datasets must be an object.")
        return

    required_common_fields = [str(v) for v in config.get("requiredCommonFields", [])]
    domain_fields = [str(v) for v in config.get("domainFields", [])]
    domain_codes_by_field: dict[str, dict[str, set[str]]] = {
        field: {} for field in domain_fields
    }
    validated_names: list[str] = []

    for spec in specs:
        name = str(spec.get("name", "unnamed"))
        rel = str(spec.get("path", ""))
        layer_id = spec.get("layerId")
        expected_source_dataset = str(spec.get("sourceDataset", name))
        expected_families = [str(v) for v in spec.get("expectedGeometryFamilies", [])]
        expected_family = expected_families[0] if len(expected_families) == 1 else None

        metadata = metadata_datasets.get(name)
        if not isinstance(metadata, dict):
            report.add_issue(
                "ERROR", "LAYER_METADATA_DATASET_MISSING",
                f"Layer metadata record is missing for dataset {name!r}.", dataset=name,
            )
            continue

        features, load_error = load_dataset(repo_root / rel)
        if load_error or features is None:
            # Dataset QA has already reported the primary problem.
            continue
        validated_names.append(name)

        if metadata.get("layerId") != layer_id:
            report.add_issue(
                "ERROR", "LAYER_METADATA_ID_MISMATCH",
                f"Layer metadata layerId does not match QA configuration for {name!r}.",
                dataset=name,
                examples=[{"expected": layer_id, "actual": metadata.get("layerId")}],
            )
        if metadata.get("sourceDataset") != expected_source_dataset:
            report.add_issue(
                "ERROR", "LAYER_METADATA_SOURCE_MISMATCH",
                f"Layer metadata sourceDataset does not match QA configuration for {name!r}.",
                dataset=name,
                examples=[{"expected": expected_source_dataset, "actual": metadata.get("sourceDataset")}],
            )
        if expected_family and metadata.get("geometryFamily") != expected_family:
            report.add_issue(
                "ERROR", "LAYER_METADATA_GEOMETRY_MISMATCH",
                f"Layer metadata geometryFamily does not match {name!r} dataset expectation.",
                dataset=name,
                examples=[{"expected": expected_family, "actual": metadata.get("geometryFamily")}],
            )
        if metadata.get("entityCount") != len(features):
            report.add_issue(
                "ERROR", "LAYER_METADATA_COUNT_MISMATCH",
                f"Layer metadata entityCount does not match exported feature count for {name!r}.",
                dataset=name,
                examples=[{"metadata": metadata.get("entityCount"), "geojson": len(features)}],
            )

        if expected_server and layer_id is not None:
            expected_source_url = f"{expected_server}/{layer_id}"
            actual_source_url = str(metadata.get("sourceUrl") or "").rstrip("/")
            if actual_source_url != expected_source_url:
                report.add_issue(
                    "ERROR", "LAYER_METADATA_URL_MISMATCH",
                    f"Layer metadata sourceUrl does not match expected public-view sublayer for {name!r}.",
                    dataset=name,
                    examples=[{"expected": expected_source_url, "actual": actual_source_url}],
                )

        availability = metadata.get("commonFieldAvailability")
        field_names = metadata.get("fieldNames")
        missing_common: list[str] = []
        if not isinstance(availability, dict):
            missing_common = list(required_common_fields)
        else:
            missing_common = [field for field in required_common_fields if availability.get(field) is not True]
        if missing_common:
            report.add_issue(
                "ERROR", "COMMON_FIELD_MISSING",
                "Required Common Entity fields are missing from ArcGIS layer metadata.",
                dataset=name, count=len(missing_common), examples=missing_common,
            )
        if not isinstance(field_names, list):
            report.add_issue(
                "ERROR", "LAYER_METADATA_FIELDS_INVALID",
                "Layer metadata fieldNames must be an array.", dataset=name,
            )
        else:
            field_name_set = {str(v) for v in field_names}
            missing_from_names = [field for field in required_common_fields if field not in field_name_set]
            if missing_from_names:
                report.add_issue(
                    "ERROR", "COMMON_FIELD_LIST_MISMATCH",
                    "Required Common Entity fields are absent from layer metadata fieldNames.",
                    dataset=name, count=len(missing_from_names), examples=missing_from_names,
                )

        domains = metadata.get("domains")
        observed_meta = metadata.get("observedValues")
        if not isinstance(domains, dict):
            report.add_issue("ERROR", "LAYER_METADATA_DOMAINS_INVALID", "Layer metadata domains must be an object.", dataset=name)
            domains = {}
        if not isinstance(observed_meta, dict):
            report.add_issue("ERROR", "LAYER_METADATA_OBSERVED_INVALID", "Layer metadata observedValues must be an object.", dataset=name)
            observed_meta = {}

        for field_name in domain_fields:
            entries = domains.get(field_name)
            codes, invalid_entries, duplicate_codes = normalize_domain_values(entries)
            domain_codes_by_field[field_name][name] = codes
            if invalid_entries:
                report.add_issue(
                    "ERROR", "DOMAIN_METADATA_INVALID",
                    f"ArcGIS coded-value metadata for {field_name} is malformed.",
                    dataset=name, count=len(invalid_entries), examples=invalid_entries,
                )
            if duplicate_codes:
                report.add_issue(
                    "ERROR", "DOMAIN_CODE_DUPLICATE",
                    f"ArcGIS coded-value metadata for {field_name} contains duplicate stored codes.",
                    dataset=name, count=len(duplicate_codes), examples=duplicate_codes,
                )
            if not codes:
                report.add_issue(
                    "WARNING", "DOMAIN_NOT_CODED",
                    f"No coded-value domain was harvested for {field_name}; future domain divergence is allowed but should be reviewed.",
                    dataset=name,
                )

            actual_values = actual_observed_values(features, field_name)
            metadata_values_raw = observed_meta.get(field_name, [])
            metadata_values = {
                str(v).strip() for v in metadata_values_raw
                if v is not None and str(v).strip()
            } if isinstance(metadata_values_raw, list) else set()
            if metadata_values != actual_values:
                report.add_issue(
                    "ERROR", "LAYER_METADATA_OBSERVED_MISMATCH",
                    f"Harvested observedValues for {field_name} do not match the exported GeoJSON.",
                    dataset=name,
                    examples=[{
                        "metadataOnly": sorted(metadata_values - actual_values)[:10],
                        "geojsonOnly": sorted(actual_values - metadata_values)[:10],
                    }],
                )
            if codes:
                outside = sorted(actual_values - codes)
                if outside:
                    report.add_issue(
                        "WARNING", "DOMAIN_VALUE_OUTSIDE_CODED_LIST",
                        f"Exported {field_name} values are not present in the current coded-value domain.",
                        dataset=name, count=len(outside), examples=outside,
                    )

        expected_attachment_summary = actual_attachment_summary(
            features, attachment_field, attachment_media_field
        )
        metadata_attachment_summary = metadata.get("attachmentSummary")
        if metadata_attachment_summary != expected_attachment_summary:
            report.add_issue(
                "ERROR", "LAYER_METADATA_ATTACHMENT_MISMATCH",
                "Layer metadata attachmentSummary does not match exported attachment_media.",
                dataset=name,
                examples=[{
                    "metadata": metadata_attachment_summary,
                    "geojson": expected_attachment_summary,
                }],
            )

    configured_names = {str(spec.get("name", "unnamed")) for spec in specs}
    extra_names = sorted(set(metadata_datasets) - configured_names)
    if extra_names:
        report.add_issue(
            "WARNING", "LAYER_METADATA_EXTRA_DATASET",
            "layers-metadata.json contains datasets not configured for publication.",
            count=len(extra_names), examples=extra_names,
        )

    comparison: dict[str, Any] = {}
    for field_name, datasets in domain_codes_by_field.items():
        code_sets = [frozenset(values) for values in datasets.values()]
        aligned = len(set(code_sets)) <= 1 if code_sets else True
        union_codes = sorted(set().union(*datasets.values()) if datasets else set())
        comparison[field_name] = {
            "alignedAcrossDatasets": aligned,
            "unionCount": len(union_codes),
            "unionCodes": union_codes,
            "datasets": {name: sorted(values) for name, values in sorted(datasets.items())},
        }
    report.domain_comparison = comparison
    report.layer_metadata = {
        "path": rel_path,
        "featureServerUrl": actual_server,
        "datasetCount": len(metadata_datasets),
        "validatedDatasets": validated_names,
        "requiredCommonFieldCount": len(required_common_fields),
        "domainFields": domain_fields,
    }
    report.summary["layerMetadataDatasetCount"] = len(metadata_datasets)
    report.summary["requiredCommonFieldCount"] = len(required_common_fields)


def validate(repo_root: Path, qa_config_path: Path, baseline_root: Path | None = None) -> tuple[QaReport, dict[str, Any]]:
    try:
        config = read_json(qa_config_path)
    except Exception as exc:
        report = QaReport(repo_root, qa_config_path)
        report.add_issue("ERROR", "QA_CONFIG_INVALID", f"Cannot parse QA configuration: {exc}")
        return report, {}

    report = QaReport(repo_root, qa_config_path)
    if config.get("schemaVersion") != 1:
        report.add_issue(
            "ERROR", "QA_CONFIG_SCHEMA_UNSUPPORTED",
            f"QA configuration schemaVersion must be 1, found {config.get('schemaVersion')!r}.",
        )

    for rel in config.get("requiredFiles", []):
        if not (repo_root / rel).exists():
            report.add_issue("ERROR", "REQUIRED_FILE_MISSING", f"Required file is missing: {rel}")

    configured_types = load_configured_types(repo_root, config, report)
    stable_id_field = config.get("stableIdField", "GlobalID")
    topic_field = config.get("topicField", "POI_Topic")
    type_field = config.get("typeField", "POI_Type")
    name_field = config.get("nameField", "POI_Name")
    attachment_field = config.get("attachmentField", "attachments")
    attachment_media_field = config.get("attachmentMediaField", "attachment_media")

    all_ids: dict[str, list[dict[str, Any]]] = defaultdict(list)
    current_ids_by_dataset: dict[str, set[str]] = {}
    observed_topics: Counter[str] = Counter()
    observed_types: Counter[str] = Counter()
    referenced_local_attachments: set[str] = set()

    specs = config.get("datasets", [])
    report.summary["datasetCount"] = len(specs)

    for spec in specs:
        name = str(spec.get("name", "unnamed"))
        rel = str(spec.get("path", ""))
        required = bool(spec.get("required", False))
        expected_families = {str(v) for v in spec.get("expectedGeometryFamilies", [])}
        path = repo_root / rel

        dataset_result: dict[str, Any] = {
            "name": name,
            "path": rel,
            "required": required,
            "status": "not-present",
            "featureCount": 0,
            "validStableIdCount": 0,
            "geometryFamilies": {},
        }

        if not path.exists():
            if required:
                report.add_issue("ERROR", "DATASET_MISSING", f"Required dataset is missing: {rel}", dataset=name)
                dataset_result["status"] = "error"
            else:
                dataset_result["status"] = "not-present"
            report.datasets.append(dataset_result)
            current_ids_by_dataset[name] = set()
            continue

        report.summary["activeDatasetCount"] += 1
        features, dataset_error = load_dataset(path)
        if dataset_error or features is None:
            report.add_issue("ERROR", "DATASET_INVALID", dataset_error or "Invalid dataset.", dataset=name)
            dataset_result["status"] = "error"
            report.datasets.append(dataset_result)
            current_ids_by_dataset[name] = set()
            continue

        dataset_result["status"] = "validated"
        dataset_result["featureCount"] = len(features)
        report.summary["entityCount"] += len(features)

        geometry_counts: Counter[str] = Counter()
        missing_ids: list[Any] = []
        invalid_ids: list[Any] = []
        missing_names: list[Any] = []
        missing_topics: list[Any] = []
        missing_types: list[Any] = []
        suspicious_types: Counter[str] = Counter()
        geometry_errors: list[Any] = []
        wrong_geometry_family: list[Any] = []
        invalid_feature_objects: list[int] = []
        attachment_field_errors: list[Any] = []
        missing_attachments: list[str] = []
        unsafe_attachment_paths: list[str] = []
        attachment_media_errors: list[Any] = []
        attachment_media_mismatches: list[Any] = []
        dataset_media_kinds: Counter[str] = Counter()
        dataset_media_storage: Counter[str] = Counter()
        dataset_ids: set[str] = set()

        for index, feature in enumerate(features):
            if not isinstance(feature, dict) or feature.get("type") != "Feature":
                invalid_feature_objects.append(index)
                continue
            props = feature.get("properties")
            if not isinstance(props, dict):
                props = {}

            object_hint = props.get("OBJECTID", index)
            family, geometry_error = validate_geometry(feature.get("geometry"))
            family_key = family or "unknown"
            geometry_counts[family_key] += 1
            report.counts["geometryFamilies"][family_key] += 1
            if geometry_error:
                geometry_errors.append({"object": object_hint, "message": geometry_error})
            if family and expected_families and family not in expected_families:
                wrong_geometry_family.append({"object": object_hint, "family": family})

            raw_id = props.get(stable_id_field)
            normalized_id = normalize_uuid(raw_id)
            if raw_id in (None, ""):
                missing_ids.append(object_hint)
            elif normalized_id is None:
                invalid_ids.append({"object": object_hint, "value": raw_id})
            else:
                dataset_ids.add(normalized_id)
                all_ids[normalized_id].append({"dataset": name, "object": object_hint})

            name_value = props.get(name_field)
            if name_value is None or not str(name_value).strip():
                missing_names.append(object_hint)

            topic_value = props.get(topic_field)
            if topic_value is None or not str(topic_value).strip():
                missing_topics.append(object_hint)
            else:
                topic_text = str(topic_value).strip()
                observed_topics[topic_text] += 1
                report.counts["topics"][topic_text] += 1

            type_value = props.get(type_field)
            if type_value is None or not str(type_value).strip():
                missing_types.append(object_hint)
            else:
                type_text = str(type_value).strip()
                observed_types[type_text] += 1
                report.counts["types"][type_text] += 1
                if type_text.lower() in SUSPICIOUS_PLACEHOLDERS:
                    suspicious_types[type_text] += 1

            attachments = props.get(attachment_field)
            if attachments is None:
                attachments = []
            if not isinstance(attachments, list):
                attachment_field_errors.append(object_hint)
                attachments = []

            for attachment in attachments:
                report.summary["attachmentReferenceCount"] += 1
                if not isinstance(attachment, str) or not attachment.strip():
                    attachment_field_errors.append(object_hint)
                    continue
                ref = attachment.strip()
                parsed = urlparse(ref)
                if parsed.scheme.lower() in REMOTE_SCHEMES:
                    report.summary["remoteAttachmentCount"] += 1
                    continue
                local_path, path_error = safe_repo_path(repo_root, ref)
                if path_error or local_path is None:
                    unsafe_attachment_paths.append(ref)
                    continue
                normalized_ref = str(local_path.relative_to(repo_root)).replace("\\", "/")
                referenced_local_attachments.add(normalized_ref)
                if local_path.exists() and local_path.is_file():
                    report.summary["localAttachmentCount"] += 1
                else:
                    report.summary["missingAttachmentCount"] += 1
                    missing_attachments.append(ref)

            media_metadata = props.get(attachment_media_field)
            if not isinstance(media_metadata, list):
                attachment_media_errors.append({"object": object_hint, "reason": f"{attachment_media_field} is not an array"})
                media_metadata = []

            media_urls: list[str] = []
            for item in media_metadata:
                if not isinstance(item, dict):
                    attachment_media_errors.append({"object": object_hint, "reason": "media item is not an object"})
                    continue
                url = item.get("url")
                kind = item.get("kind")
                storage = item.get("storage")
                if not isinstance(url, str) or not url.strip():
                    attachment_media_errors.append({"object": object_hint, "reason": "media item is missing url"})
                    continue
                url = url.strip()
                media_urls.append(url)
                if kind not in {"image", "audio", "video", "other"}:
                    attachment_media_errors.append({"object": object_hint, "url": url, "reason": f"invalid kind: {kind!r}"})
                    continue
                if storage not in {"local", "remote"}:
                    attachment_media_errors.append({"object": object_hint, "url": url, "reason": f"invalid storage: {storage!r}"})
                    continue
                parsed = urlparse(url)
                is_remote = parsed.scheme.lower() in REMOTE_SCHEMES
                if storage == "remote" and not is_remote:
                    attachment_media_errors.append({"object": object_hint, "url": url, "reason": "remote storage must use http(s) URL"})
                if storage == "local" and is_remote:
                    attachment_media_errors.append({"object": object_hint, "url": url, "reason": "local storage must use repository-relative path"})
                report.summary["mediaMetadataCount"] += 1
                report.counts["mediaKinds"][kind] += 1
                report.counts["mediaStorage"][storage] += 1
                dataset_media_kinds[kind] += 1
                dataset_media_storage[storage] += 1

            attachment_refs = [ref.strip() for ref in attachments if isinstance(ref, str) and ref.strip()]
            if sorted(media_urls) != sorted(attachment_refs):
                attachment_media_mismatches.append({
                    "object": object_hint,
                    "attachmentCount": len(attachment_refs),
                    "mediaMetadataCount": len(media_urls),
                })

        dataset_result["validStableIdCount"] = len(dataset_ids)
        dataset_result["geometryFamilies"] = dict(sorted(geometry_counts.items()))
        dataset_result["mediaKinds"] = dict(sorted(dataset_media_kinds.items()))
        dataset_result["mediaStorage"] = dict(sorted(dataset_media_storage.items()))
        current_ids_by_dataset[name] = dataset_ids

        if invalid_feature_objects:
            report.add_issue(
                "ERROR", "INVALID_FEATURE", "Dataset contains entries that are not valid GeoJSON Features.",
                dataset=name, count=len(invalid_feature_objects), examples=invalid_feature_objects,
            )
        if geometry_errors:
            report.add_issue(
                "ERROR", "INVALID_GEOMETRY", "Dataset contains invalid or unsupported geometries.",
                dataset=name, count=len(geometry_errors), examples=geometry_errors,
            )
        if wrong_geometry_family:
            report.add_issue(
                "ERROR", "UNEXPECTED_GEOMETRY_FAMILY",
                f"Dataset contains geometry families outside the configured expectation: {sorted(expected_families)}.",
                dataset=name, count=len(wrong_geometry_family), examples=wrong_geometry_family,
            )
        if missing_ids:
            report.add_issue(
                "ERROR", "STABLE_ID_MISSING", f"Features are missing {stable_id_field}.",
                dataset=name, count=len(missing_ids), examples=missing_ids,
            )
        if invalid_ids:
            report.add_issue(
                "ERROR", "STABLE_ID_INVALID", f"Features contain invalid {stable_id_field} UUID values.",
                dataset=name, count=len(invalid_ids), examples=invalid_ids,
            )
        if missing_names:
            report.add_issue(
                "WARNING", "NAME_MISSING", f"Features are missing {name_field}.",
                dataset=name, count=len(missing_names), examples=missing_names,
            )
        if missing_topics:
            report.add_issue(
                "WARNING", "TOPIC_MISSING", f"Features are missing {topic_field}.",
                dataset=name, count=len(missing_topics), examples=missing_topics,
            )
        if missing_types:
            report.add_issue(
                "WARNING", "TYPE_MISSING", f"Features are missing {type_field}.",
                dataset=name, count=len(missing_types), examples=missing_types,
            )
        if suspicious_types:
            report.add_issue(
                "WARNING", "TYPE_PLACEHOLDER_VALUE",
                "POI_Type contains placeholder-like values that should be reviewed in ArcGIS Online.",
                dataset=name, count=sum(suspicious_types.values()),
                examples=[{"value": key, "count": value} for key, value in suspicious_types.items()],
            )
        if attachment_field_errors:
            report.add_issue(
                "ERROR", "ATTACHMENT_FIELD_INVALID",
                f"{attachment_field} must be an array of non-empty strings when present.",
                dataset=name, count=len(attachment_field_errors), examples=attachment_field_errors,
            )
        if unsafe_attachment_paths:
            report.add_issue(
                "ERROR", "ATTACHMENT_PATH_UNSAFE",
                "Attachment references contain absolute or repository-escaping paths.",
                dataset=name, count=len(unsafe_attachment_paths), examples=unsafe_attachment_paths,
            )
        if missing_attachments:
            report.add_issue(
                "ERROR", "ATTACHMENT_FILE_MISSING",
                "Local attachment references point to files that do not exist.",
                dataset=name, count=len(missing_attachments), examples=missing_attachments,
            )
        if attachment_media_errors:
            report.add_issue(
                "ERROR", "ATTACHMENT_MEDIA_INVALID",
                f"{attachment_media_field} must contain valid media metadata objects.",
                dataset=name, count=len(attachment_media_errors), examples=attachment_media_errors,
            )
        if attachment_media_mismatches:
            report.add_issue(
                "ERROR", "ATTACHMENT_MEDIA_MISMATCH",
                f"{attachment_media_field} URLs must match the canonical {attachment_field} references one-to-one.",
                dataset=name, count=len(attachment_media_mismatches), examples=attachment_media_mismatches,
            )

        report.datasets.append(dataset_result)

    attachments_root = repo_root / "data" / "attachments"
    orphan_local_attachments: list[str] = []
    if attachments_root.exists() and attachments_root.is_dir():
        for local_file in attachments_root.rglob("*"):
            if not local_file.is_file() or local_file.name == ".gitkeep":
                continue
            rel = str(local_file.relative_to(repo_root)).replace("\\", "/")
            if rel not in referenced_local_attachments:
                orphan_local_attachments.append(rel)

    report.summary["orphanAttachmentCount"] = len(orphan_local_attachments)
    if orphan_local_attachments:
        report.add_issue(
            "ERROR",
            "ATTACHMENT_FILE_ORPHAN",
            "Local attachment files exist but are not referenced by any current exported entity.",
            count=len(orphan_local_attachments),
            examples=orphan_local_attachments,
        )

    duplicate_ids = {key: refs for key, refs in all_ids.items() if len(refs) > 1}
    report.summary["stableIdCount"] = len(all_ids)
    if duplicate_ids:
        examples = [{"entityId": key, "references": refs} for key, refs in list(duplicate_ids.items())[:10]]
        report.add_issue(
            "ERROR", "STABLE_ID_DUPLICATE",
            "Stable Entity IDs must be unique across all active spatial datasets.",
            count=len(duplicate_ids), examples=examples,
        )

    unconfigured_types = sorted(set(observed_types) - configured_types)
    if unconfigured_types:
        report.add_issue(
            "WARNING", "TYPE_STYLE_MISSING",
            "POI Types exist in exported data but have no explicit style in config.json; the website will use its default style.",
            count=len(unconfigured_types),
            examples=[{"value": value, "count": observed_types[value]} for value in unconfigured_types],
        )

    validate_layers_metadata(
        repo_root, config, specs, attachment_field, attachment_media_field, report
    )

    validate_sidecar(
        repo_root,
        config.get("metadataSidecarPath", "data/site/poi-meta.json"),
        set(all_ids),
        report,
    )

    if baseline_root is not None:
        compare_baseline(repo_root, baseline_root, specs, stable_id_field, current_ids_by_dataset, report)

    return report, config


def write_report(report: QaReport, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report.as_dict(), handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def markdown_summary(report: QaReport) -> str:
    status_icon = {"PASS": "✅", "WARNING": "⚠️", "ERROR": "❌"}[report.status]
    lines = [
        "## POIS Travel Science — Data QA",
        "",
        f"**Status:** {status_icon} {report.status}",
        "",
        "| Metric | Count |",
        "| --- | ---: |",
        f"| Active datasets | {report.summary['activeDatasetCount']} |",
        f"| Layer metadata datasets | {report.summary.get('layerMetadataDatasetCount', 0)} |",
        f"| Entities | {report.summary['entityCount']} |",
        f"| Stable IDs | {report.summary['stableIdCount']} |",
        f"| Attachment references | {report.summary['attachmentReferenceCount']} |",
        f"| Attachment media metadata | {report.summary['mediaMetadataCount']} |",
        f"| Images | {report.counts['mediaKinds'].get('image', 0)} |",
        f"| Audio | {report.counts['mediaKinds'].get('audio', 0)} |",
        f"| Video | {report.counts['mediaKinds'].get('video', 0)} |",
        f"| Other media | {report.counts['mediaKinds'].get('other', 0)} |",
        f"| Missing local attachments | {report.summary['missingAttachmentCount']} |",
        f"| Orphan local attachments | {report.summary['orphanAttachmentCount']} |",
        f"| Warnings | {report.summary['warningCount']} |",
        f"| Errors | {report.summary['errorCount']} |",
    ]
    if report.deltas is not None:
        lines += [
            f"| Added since baseline | {report.deltas['added']} |",
            f"| Removed since baseline | {report.deltas['removed']} |",
        ]
    if report.domain_comparison:
        lines += ["", "### Domain alignment", ""]
        for field_name, info in report.domain_comparison.items():
            status = "aligned" if info.get("alignedAcrossDatasets") else "divergent (allowed)"
            lines.append(f"- **{field_name}**: {status}; union {info.get('unionCount', 0)} coded values.")
    if report.issues:
        lines += ["", "### Issues", ""]
        for issue in report.issues:
            icon = "❌" if issue["severity"] == "ERROR" else "⚠️"
            suffix = f" ({issue['count']})" if "count" in issue else ""
            lines.append(f"- {icon} **{issue['code']}**{suffix}: {issue['message']}")
    return "\n".join(lines) + "\n"


def append_github_step_summary(text: str) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    try:
        with open(summary_path, "a", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
    except OSError:
        pass


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate POIS Travel Science generated data.")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[1]),
        help="Repository root. Defaults to the parent of scripts/.",
    )
    parser.add_argument(
        "--config",
        default="scripts/qa_config.json",
        help="QA configuration path relative to the repository root.",
    )
    parser.add_argument(
        "--report",
        default=None,
        help="Override report output path. Defaults to reportPath from QA configuration.",
    )
    parser.add_argument(
        "--baseline-root",
        default=None,
        help="Optional previous repository snapshot for added/removed stable-ID comparison.",
    )
    parser.add_argument(
        "--fail-on-warnings",
        action="store_true",
        help="Exit with code 1 when warnings are present, even if there are no errors.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    qa_config_path = (repo_root / args.config).resolve()
    baseline_root = Path(args.baseline_root).resolve() if args.baseline_root else None

    report, config = validate(repo_root, qa_config_path, baseline_root)
    report_rel = args.report or config.get("reportPath", "data/derived/qa-report.json")
    report_path = Path(report_rel)
    if not report_path.is_absolute():
        report_path = repo_root / report_path
    write_report(report, report_path)

    summary = markdown_summary(report)
    append_github_step_summary(summary)

    print(f"Data QA status: {report.status}")
    print(f"Entities: {report.summary['entityCount']}")
    print(f"Warnings: {report.summary['warningCount']}")
    print(f"Errors: {report.summary['errorCount']}")
    print(f"Report: {report_path}")
    if report.deltas is not None:
        print(f"Added since baseline: {report.deltas['added']}")
        print(f"Removed since baseline: {report.deltas['removed']}")

    if report.summary["errorCount"] > 0:
        return 1
    if args.fail_on_warnings and report.summary["warningCount"] > 0:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
