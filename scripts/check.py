#!/usr/bin/env python3
"""Repository-level source, fixture, and publication-safety checks."""

import json
import os
from pathlib import Path
import py_compile
import re
import shutil
import time
import subprocess
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {".git", "node_modules", "__pycache__", "run", "results", ".claude"}


def source_files(suffix):
    return [path for path in ROOT.rglob(f"*{suffix}") if not IGNORED_PARTS.intersection(path.parts)]


def run(command, **kwargs):
    subprocess.run(command, cwd=ROOT, check=True, **kwargs)


for path in source_files(".py"):
    py_compile.compile(str(path), doraise=True)

for path in source_files(".mjs"):
    run(["node", "--check", str(path)])

for path in source_files(".sh"):
    run(["bash", "-n", str(path)])

run([sys.executable, "-m", "unittest", "discover", "-s", "pipelines/github", "-p", "test_*.py"], stdout=subprocess.DEVNULL)
run([
    sys.executable, "pipelines/github/run_campaign.py", "--dry-run",
    "--campaign", "pipelines/github/campaigns/agent-systems-v1.json",
], stdout=subprocess.DEVNULL)

with tempfile.TemporaryDirectory(prefix="siso-foundry-check-") as directory:
    env = dict(os.environ)
    env["FOUNDRY_TOPICS_DB"] = str(Path(directory) / "topics.sqlite")
    topics = ROOT / "packages" / "research-topics" / "topics.py"
    run([sys.executable, str(topics), "init"], env=env, stdout=subprocess.DEVNULL)
    run([sys.executable, str(topics), "list"], env=env, stdout=subprocess.DEVNULL)

manifest = json.loads((ROOT / "datasets" / "manifest.json").read_text())
assert manifest["work_id"].startswith("gls:work:")
assert manifest["assets"]
for asset in manifest["assets"]:
    assert asset["observed_bytes"] >= 0
    assert asset["publication_state"]
    assert asset["required_release_receipts"]

agency_snapshot = json.loads((ROOT / "intelligence" / "agency" / "snapshot.json").read_text())
assert agency_snapshot["record_type"] == "agency_intelligence_snapshot"
assert agency_snapshot["work_id"] == manifest["work_id"]
assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", agency_snapshot["observed_at"])
assert agency_snapshot["publication_state"] == "metadata_only"
assert agency_snapshot["payload_materialization"] == "not_materialized"
assert agency_snapshot["source_components"]
database_receipt = agency_snapshot["source_components"][0]
assert database_receipt["logical_asset_id"] == "foundry-github-identity-live"
assert database_receipt["observed_bytes"] == 1879339008
assert re.fullmatch(r"[0-9a-f]{64}", database_receipt["sha256"])
assert database_receipt["wal_bytes"] == 0

corpus = agency_snapshot["corpus"]
adoption = corpus["adoption"]
assert adoption["total"] == sum(adoption[key] for key in ("promote", "confirm", "demote", "unresolved"))
adoption_receipt = database_receipt["query_receipts"]["adoption"]
assert adoption["total"] == adoption_receipt["row_count"]
assert adoption["promote"] == adoption_receipt["promote_rows"]
assert adoption["confirm"] == adoption_receipt["confirm_rows"]
assert adoption["demote"] == adoption_receipt["demote_rows"]
assert adoption["unresolved"] == adoption_receipt["unresolved_rows"]
proof = corpus["proof_selection"]
assert proof["rows"] == sum(proof[key] for key in ("promote", "confirm", "demote"))
proven_pick_receipt = agency_snapshot["source_components"][1]
assert proof["rows"] == proven_pick_receipt["rows_excluding_header"]
assert re.fullmatch(r"[0-9a-f]{64}", proven_pick_receipt["sha256"])
graph = corpus["capability_graph"]
assert graph["edges"] == graph["hard_edges"] + graph["soft_edges"]
graph_receipt = database_receipt["query_receipts"]["capability_graph"]
assert graph["nodes"] == graph_receipt["node_rows"]
assert graph["edges"] == graph_receipt["edge_rows"]
assert graph["hard_edges"] == graph_receipt["hard_edge_rows"]
assert graph["soft_edges"] == graph_receipt["soft_edge_rows"]
assert graph["closure_rows"] == graph_receipt["closure_rows"]
cards = corpus["reuse_bank"]
verified_cards = cards["verified_harness_subset"]
assert cards["contract_cards_total"] >= verified_cards["total"]
assert verified_cards["total"] == verified_cards["self_smoke"] + verified_cards["import_smoke"]
assert verified_cards["total"] >= verified_cards["trust_rung_3"]
card_receipt = database_receipt["query_receipts"]["contract_cards"]
assert cards["contract_cards_total"] == card_receipt["row_count"]
assert verified_cards["total"] == card_receipt["trust_and_smoke_populated_rows"]
assert agency_snapshot["agency_candidate_ideas"]["evidence_state"] == "operator_nominated_pending_direct_source_review"
assert agency_snapshot["agency_candidate_ideas"]["clusters"]
assert agency_snapshot["siso_control_plane_gaps"]

value_matrix = json.loads((ROOT / "intelligence" / "agency" / "value-matrix.json").read_text())
assert value_matrix["record_type"] == "agency_os_value_matrix"
assert value_matrix["work_id"] == manifest["work_id"]
assert value_matrix["unit_of_analysis"] == "repository_x_siso_use_case_x_adoption_route"
assert value_matrix["source_universe"]["matrix_entries"] == len(value_matrix["entries"])
assert value_matrix["source_universe"]["deduplicated_repositories"] >= len(value_matrix["entries"])

value_weights = value_matrix["score_model"]["value_weights"]
feasibility_weights = value_matrix["score_model"]["feasibility_weights"]
assert sum(value_weights.values()) == 100
assert sum(feasibility_weights.values()) == 100

entry_ids = set()
authority_groups = set()
evidence_states = value_matrix["evidence_states"]
evidence_rank = {state: index for index, state in enumerate(evidence_states)}
for entry in value_matrix["entries"]:
    assert entry["entry_id"] not in entry_ids
    entry_ids.add(entry["entry_id"])
    authority_groups.add(entry["authority_group"])
    assert re.fullmatch(r"[^/\s]+/[^/\s]+", entry["repository"])
    assert entry["evidence_state"] in evidence_rank
    assert entry["agent_operations"]
    assert entry["hard_gates"]
    assert entry["evidence"]

    value = entry["value"]
    feasibility = entry["feasibility"]
    assert set(value) == set(value_weights) | {"total"}
    assert set(feasibility) == set(feasibility_weights) | {"total"}
    assert all(isinstance(value[key], int) and 0 <= value[key] <= 5 for key in value_weights)
    assert all(isinstance(feasibility[key], int) and 0 <= feasibility[key] <= 5 for key in feasibility_weights)
    calculated_value = round(sum(value[key] * weight / 5 for key, weight in value_weights.items()))
    calculated_feasibility = round(sum(feasibility[key] * weight / 5 for key, weight in feasibility_weights.items()))
    assert value["total"] == calculated_value
    assert feasibility["total"] == calculated_feasibility
    assert entry["priority_index"] == round(calculated_value * calculated_feasibility / 100)

    if entry["classification"] == "god_source":
        assert value["total"] >= 85
        assert feasibility["total"] >= 65
        assert value["agent_leverage"] >= 4
        assert value["agency_edition"] >= 4
        assert value["client_delivery"] >= 4
        assert evidence_rank[entry["evidence_state"]] >= evidence_rank["source_read"]

assert len(authority_groups) == len(value_matrix["entries"])

# Agency OS expansion coverage inventory: repository-level deduplication and
# evidence gates.  This is deliberately checked against the lane receipt's
# 497 application rows so aggregate percentages cannot silently drift.
coverage = json.loads((ROOT / "intelligence" / "agency" / "coverage-inventory.json").read_text())
cap_map = json.loads((ROOT / "intelligence" / "agency" / "capability-pillar-map.json").read_text())
assert cap_map["record_type"] == "agency_os_capability_pillar_map"
assert cap_map["counts"]["capabilities"] == 189
assert len(cap_map["capabilities"]) == 189 == len({c["capability_id"] for c in cap_map["capabilities"]})
assert all(c["canonical_pillars"] and set(c["canonical_pillars"]).issubset(set(cap_map["canonical_pillars"])) for c in cap_map["capabilities"])
assert all(c["raw_slice"] and c["rationale"].endswith(".") for c in cap_map["capabilities"])
atlas_path = ROOT.parents[2] / ".agents" / "runs" / "agency-os-god-source-expansion-20260802" / "lane-b-capability-atlas.jsonl"
# The lane receipt is an external run artifact that lives on the machine that ran the lane; check it where it exists.
if atlas_path.exists():
    atlas_ids = {json.loads(line)["capability_id"] for line in atlas_path.read_text().splitlines() if line.strip()}
    assert {c["capability_id"] for c in cap_map["capabilities"]} == atlas_ids
assert coverage["record_type"] == "agency_os_coverage_inventory"
assert coverage["counts"]["candidate_application_rows"] == 497
assert coverage["counts"]["frontier_rows"] == 30
assert coverage["counts"]["atlas_capability_rows"] == 189
coverage_rows = coverage["rows"]
assert coverage["counts"]["unique_repositories"] == len(coverage_rows) == len({r["repository"] for r in coverage_rows})
assert coverage["coverage"]["inferred_rows_counted_as_verified"] == 0
assert all(r["evidence_grade"] in {"metadata", "inferred", "source-read", "adversarial-confirmed"} for r in coverage_rows)
assert all(r["verticals"] and r["categories"] for r in coverage_rows)
assert all("license" in r and "source_refs" in r and "analyzed" in r for r in coverage_rows)
assert sum(r["application_row_count"] for r in coverage_rows) == 497
assert sum(r["frontier_row_count"] for r in coverage_rows) == 30
assert coverage["coverage"]["adversarial_confirmed_unique_repositories"] == sum(r["analyzed"]["adversarial_confirmed"] for r in coverage_rows)
assert coverage["coverage"]["source_read_unique_repositories"] == sum(r["analyzed"]["source_read"] for r in coverage_rows)
assert coverage["coverage"]["reusable_analysis_unique_repositories"] <= coverage["counts"]["unique_repositories"]
assert coverage["coverage"]["source_read_candidate_application_rows"] == 89
assert coverage["counts"]["multi_vertical_projects"] == sum(len(r["canonical_verticals"]) > 1 for r in coverage_rows)
canonical = coverage["canonical_pillars"]
assert len(canonical) == 12 and len(set(canonical)) == 12
assert coverage["counts"]["unmapped_vertical_labels"] == 0
assert set(coverage["vertical_coverage"]) == set(canonical)
for row in coverage_rows:
    assert row["canonical_verticals"] and set(row["canonical_verticals"]).issubset(set(canonical))
    assert row["raw_vertical_labels"]
assert all("slice" not in r["canonical_verticals"] for r in coverage_rows)
assert all(set(r["canonical_verticals"]).issubset(set(canonical)) for r in coverage_rows)
for pillar, detail in coverage["vertical_coverage"].items():
    assert detail["repository_count"] == len(detail["projects"]) == len(set(detail["projects"]))

# Domain research: records are rebuilt from append-only observations, ids are unique, and the lookup answers.
for records_path in sorted((ROOT / "research").glob("*/records.jsonl")):
    rows = [json.loads(line) for line in records_path.read_text().split("\n") if line.strip()]
    ids = [r["id"] for r in rows]
    assert len(ids) == len(set(ids)), f"duplicate record id in {records_path}"
    assert len({r["key"] for r in rows}) == len(rows), f"duplicate record key in {records_path}"
    for r in rows:
        assert r["url"] and r["title"] and r["domain"] == records_path.parent.name, r
with tempfile.TemporaryDirectory() as usage_root:
    env = {**os.environ, "FOUNDRY_DATA": usage_root}
    sample = next((json.loads(l) for p in sorted((ROOT / "research").glob("*/records.jsonl")) for l in p.read_text().split("\n") if l.strip()), None)
    if sample:
        found = subprocess.run([sys.executable, "bin/foundry", "find", sample["title"], "--no-items", "--json"], cwd=ROOT, env=env, capture_output=True, text=True)
        assert found.returncode == 0 and any(r["id"] == sample["id"] for r in json.loads(found.stdout)["results"][:50]), found.stdout[:300]
    missing = subprocess.run([sys.executable, "bin/foundry", "find", "zzqqxnotathing"], cwd=ROOT, env=env, capture_output=True, text=True)
    assert missing.returncode == 3, missing.stdout
    assert (Path(usage_root) / "usage" / "find.jsonl").read_text().count("\n") >= 1, "lookups are not counted"

# Research OS: isolated checkout fixtures never write curation or questions into this repository.
with tempfile.TemporaryDirectory(prefix="foundry-research-check-") as directory:
    fixture = Path(directory)
    (fixture / "bin").mkdir()
    shutil.copyfile(ROOT / "bin" / "foundry", fixture / "bin" / "foundry")
    research = fixture / "research"
    base = research / "voice"
    (base / "observations").mkdir(parents=True)
    (base / "curation").mkdir()
    records = [{"id": f"fixture-{n}", "title": f"Fixture {n}", "url": f"https://example.org/{n}",
                "github": "sample/repo" if n == 1 else "", "area": "stt" if n == 1 else "tts"} for n in range(4)]
    (base / "records.jsonl").write_text("".join(json.dumps(r) + "\n" for r in records))
    (base / "curation" / "existing.jsonl").write_text(json.dumps({"id": "fixture-0", "verdict": "drop", "note": "done"}) + "\n")
    shutil.copyfile(ROOT / "research" / "sources.json", research / "sources.json")
    env = {**os.environ, "FOUNDRY_DATA": str(fixture / "data")}

    def research_cli(*args):
        return subprocess.run([sys.executable, str(fixture / "bin" / "foundry"), *args],
                              cwd=fixture, env=env, capture_output=True, text=True)

    batches = fixture / "batches"
    emitted = research_cli("curate", "emit", "--domain", "voice", "--out", str(batches), "--batch", "2")
    assert emitted.returncode == 0, emitted.stderr
    manifest = json.loads((batches / "manifest.json").read_text())
    assert manifest["domain"] == "voice" and list(manifest["batches"]) == ["batch-001.jsonl", "batch-002.jsonl"]
    assert [i for ids in manifest["batches"].values() for i in ids] == ["fixture-1", "fixture-2", "fixture-3"]
    assert set(json.loads((batches / "batch-001.jsonl").read_text().split("\n")[0])) == {
        "id", "title", "url", "github", "stars", "area", "kind", "licence", "why", "date"}
    exact = {}
    for name, ids in manifest["batches"].items():
        rows = [{"id": rid, "verdict": "keep", "rank": 4} if rid != "fixture-3" else
                {"id": rid, "verdict": "drop", "note": "off topic"} for rid in ids]
        path = batches / name.replace(".jsonl", ".verdicts.jsonl")
        exact[path] = "".join(json.dumps(r) + "\n" for r in rows)
        path.write_text(exact[path])
    first = next(iter(exact))
    first.write_text(exact[first] + json.dumps({"id": "extra", "verdict": "keep", "rank": 3}) + "\n")
    rejected = research_cli("curate", "ingest", "--domain", "voice", "--name", "test", str(batches))
    assert rejected.returncode == 1 and "extra id extra" in rejected.stderr, rejected
    assert not (base / "curation" / "test.jsonl").exists()
    first.write_text('{"id":"fixture-1","verdict":"keep","rank":true}\n'
                     '{"id":"fixture-1","verdict":"invalid"}\n'
                     '{"id":"extra","verdict":"drop"}\nnot-json\n')
    rejected = research_cli("curate", "ingest", "--domain", "voice", "--name", "test", str(batches))
    assert rejected.returncode == 1 and all(problem in rejected.stderr for problem in (
        "integer rank", "duplicate id", "verdict must", "drop needs", "not JSON", "missing id", "extra id")), rejected.stderr
    assert not (base / "curation" / "test.jsonl").exists()
    first.write_text(exact[first])
    accepted = research_cli("curate", "ingest", "--domain", "voice", "--name", "test", str(batches))
    assert accepted.returncode == 0 and "keep: 2, drop: 1" in accepted.stdout and "4: 2" in accepted.stdout, accepted.stderr
    target = base / "curation" / "test.jsonl"
    saved = target.read_text()
    assert len(saved.splitlines()) == 3
    assert research_cli("curate", "ingest", "--domain", "voice", "--name", "test", str(batches)).returncode == 1
    assert target.read_text() == saved
    assert research_cli("curate", "ingest", "--domain", "voice", "--name", "test", str(batches), "--force").returncode == 0
    selected = fixture / "selected"
    # Before any curation for this selector, the matching repo is fixture-1.
    target.unlink()
    assert research_cli("curate", "emit", "--domain", "voice", "--out", str(selected), "--area", "stt", "--only-github").returncode == 0
    assert json.loads((selected / "manifest.json").read_text())["batches"] == {"batch-001.jsonl": ["fixture-1"]}

    dry = research_cli("refresh", "--dry-run")
    sources = json.loads((research / "sources.json").read_text())["sources"]
    assert dry.returncode == 0 and all(s["name"] + ": never run before" in dry.stdout for s in sources), dry.stderr
    assert "--domain ui" in dry.stdout and "--domain agent-bases" in dry.stdout and "--domain voice" in dry.stdout
    state = fixture / "data" / "research" / "refresh-state.json"
    assert not state.exists(), "dry-run wrote refresh state"
    state.parent.mkdir(parents=True)
    state.write_text(json.dumps({s["name"]: {"last_run": time.time()} for s in sources}))
    assert research_cli("refresh", "--due", "--dry-run").stdout == ""
    assert "open-asr:" in research_cli("refresh", "open-asr", "--dry-run").stdout
    assert research_cli("refresh", "unknown-fixture-source", "--dry-run").returncode == 2
    assert research_cli("refresh", "--all", "--dry-run").stdout.count("days since last run") == len(sources)

    created = research_cli("question", "new", "Fixture local stt choice?", "--domain", "voice", "--asked-by", "tester")
    assert created.returncode == 0, created.stderr
    question = fixture / created.stdout.strip()
    assert "status: open" in question.read_text()
    assert research_cli("question", "new", "Fixture local stt choice?", "--domain", "voice").returncode == 1
    question.write_text(question.read_text().replace("status: open", "status: answered").replace("answered: ", "answered: 2000-01-01")
                        .replace("recheck: ", "recheck: 2000-01-02").replace("## Answer\n", "## Answer\nFirst line\nSecond line\nThird line\nFourth line\n"))
    answer = research_cli("ask", "fixture", "local", "stt", "--domain", "voice", "--json")
    assert answer.returncode == 0, answer.stderr
    hit = json.loads(answer.stdout)["results"][0]
    assert hit["status"] == "answered" and hit["recheck_due"] and hit["answer"] == ["First line", "Second line", "Third line"]
    assert "RECHECK DUE" in research_cli("ask", "fixture", "stt").stdout
    assert research_cli("ask", "zzqqxnotathing").returncode == 3
    assert research_cli("ask", "fixture", "--domain", "ui").returncode == 3
    (base / "notes").mkdir()
    (base / "notes" / "local-stt.md").write_text("# Speech choice\n\nFirst note line\nSecond note line\nThird note line\nFourth note line\n")
    note = json.loads(research_cli("ask", "local", "stt", "--json").stdout)["results"]
    assert any(r["status"] == "note" and r["answer"] == ["First note line", "Second note line", "Third note line"] for r in note)
    lookups = [json.loads(line) for line in (fixture / "data" / "usage" / "find.jsonl").read_text().splitlines()]
    assert lookups and all(row["cmd"] == "ask" for row in lookups)

publication_patterns = [
    re.compile("/" + "Users" + "/"),
    re.compile("SISO_" + "Workspace"),
    re.compile("BEGIN (?:RSA |OPENSSH |EC |DSA )?" + "PRIVATE KEY"),
    re.compile("(?<![A-Za-z0-9])(?:ghp|github_pat|sk)" + "-[A-Za-z0-9_-]{16,}"),
]
for path in ROOT.rglob("*"):
    if IGNORED_PARTS.intersection(path.parts):
        continue
    if path.is_symlink():
        text = os.readlink(path)
    elif path.is_file():
        try:
            text = path.read_text()
        except UnicodeDecodeError:
            continue
    else:
        continue
    for pattern in publication_patterns:
        if pattern.search(text):
            raise SystemExit(f"publication safety match {pattern.pattern!r} in {path.relative_to(ROOT)}")

print(f"FOUNDRY_CHECK_OK ({len(source_files('.py'))} Python files)")
