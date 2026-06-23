import csv
from pathlib import Path


IN_PATH = Path("data/v1/gold/heldout_role_eval_v2.csv")
OUT_PATH = Path("data/v1/gold/heldout_full_extraction_gold_v2.csv")

FIELDNAMES = [
    "segment_id",
    "title",
    "text",
    "gold_role",
    "gold_entities",
    "gold_operative_status",
    "gold_relation",
    "gold_answer_relevant",
    "notes",
]

GOLD_FIELDS = {
    "HELDOUT2_S0001": ("AI safety evaluation; policy context; risk management", "DESCRIPTIVE", "sets_context", "NO"),
    "HELDOUT2_S0002": ("model release governance; evidence selection; human review; audit trail", "DESCRIPTIVE", "sets_context", "NO"),
    "HELDOUT2_S0003": ("privacy; consent boundary; RouteMap", "DESCRIPTIVE", "sets_context", "MAYBE"),
    "HELDOUT2_S0004": ("retrieval trace; route segment; RouteMap", "DESCRIPTIVE", "sets_context", "MAYBE"),
    "HELDOUT2_S0005": ("agent memory; benchmark; risk management; source context", "DESCRIPTIVE", "sets_context", "NO"),
    "HELDOUT2_S0006": ("tool-use security; permission boundary; incident response", "DESCRIPTIVE", "sets_context", "NO"),
    "HELDOUT2_S0007": ("benchmark; source context; gold labels; mismatch review", "DESCRIPTIVE", "sets_context", "NO"),
    "HELDOUT2_S0008": ("evidence selection; policy context; human review", "DESCRIPTIVE", "sets_context", "MAYBE"),
    "HELDOUT2_S0009": ("model release governance; audit trail; human review", "DESCRIPTIVE", "sets_context", "NO"),
    "HELDOUT2_S0010": ("incident response; source context; human review", "DESCRIPTIVE", "sets_context", "NO"),
    "HELDOUT2_S0011": ("AI safety evaluation; evaluation; audit trail", "ACTIVE", "asserts", "YES"),
    "HELDOUT2_S0012": ("model release governance; evidence selection; risk management", "ACTIVE", "asserts", "YES"),
    "HELDOUT2_S0013": ("consent boundary; permission boundary; answer support", "ACTIVE", "asserts", "YES"),
    "HELDOUT2_S0014": ("retrieval trace; answer support; evidence selection", "ACTIVE", "asserts", "YES"),
    "HELDOUT2_S0015": ("agent memory; route provenance; source context", "ACTIVE", "asserts", "YES"),
    "HELDOUT2_S0016": ("controls; evidence selection; human review", "ACTIVE", "asserts", "YES"),
    "HELDOUT2_S0017": ("benchmark; source context; route segment", "ACTIVE", "asserts", "YES"),
    "HELDOUT2_S0018": ("human review; evidence selection; retrieval trace", "ACTIVE", "asserts", "YES"),
    "HELDOUT2_S0019": ("tool-use security; permission boundary; controls", "ACTIVE", "asserts", "YES"),
    "HELDOUT2_S0020": ("audit trail; answer support; evaluation", "ACTIVE", "asserts", "YES"),
    "HELDOUT2_S0021": ("route provenance; source context; evidence selection; answer support", "DESCRIPTIVE", "defines", "YES"),
    "HELDOUT2_S0022": ("retrieval trace; evidence selection; answer support", "DESCRIPTIVE", "defines", "YES"),
    "HELDOUT2_S0023": ("consent boundary; permission boundary; privacy", "DESCRIPTIVE", "defines", "YES"),
    "HELDOUT2_S0024": ("model release governance; evaluation; risk management", "DESCRIPTIVE", "defines", "YES"),
    "HELDOUT2_S0025": ("agent memory; route extraction; source context", "DESCRIPTIVE", "defines", "YES"),
    "HELDOUT2_S0026": ("route segment; route extraction; RouteMap", "DESCRIPTIVE", "defines", "YES"),
    "HELDOUT2_S0027": ("answer support; evidence selection; retrieval trace", "DESCRIPTIVE", "defines", "YES"),
    "HELDOUT2_S0028": ("audit trail; human review; model release governance", "DESCRIPTIVE", "defines", "YES"),
    "HELDOUT2_S0029": ("controls; tool-use security; permission boundary", "DESCRIPTIVE", "defines", "YES"),
    "HELDOUT2_S0030": ("human review; evidence selection; controls", "DESCRIPTIVE", "defines", "YES"),
    "HELDOUT2_S0031": ("answer support; retrieval trace; human review", "ACTIVE", "recommends", "YES"),
    "HELDOUT2_S0032": ("model release governance; evidence selection; human review", "ACTIVE", "recommends", "YES"),
    "HELDOUT2_S0033": ("consent boundary; permission boundary; evidence selection", "ACTIVE", "maps_to", "YES"),
    "HELDOUT2_S0034": ("agent memory; route provenance; source context", "ACTIVE", "recommends", "YES"),
    "HELDOUT2_S0035": ("tool-use security; permission boundary; route segment", "ACTIVE", "requires", "YES"),
    "HELDOUT2_S0036": ("incident response; retrieval trace; controls", "ACTIVE", "maps_to", "YES"),
    "HELDOUT2_S0037": ("benchmark; policy context; route segment", "ACTIVE", "recommends", "YES"),
    "HELDOUT2_S0038": ("human review; evidence selection; answer support", "ACTIVE", "recommends", "YES"),
    "HELDOUT2_S0039": ("audit trail; answer support; human review", "ACTIVE", "recommends", "YES"),
    "HELDOUT2_S0040": ("route segment; evidence selection; human review", "ACTIVE", "recommends", "YES"),
    "HELDOUT2_S0041": ("evaluation; route provenance; answer support", "DESCRIPTIVE", "supports_retrieval", "YES"),
    "HELDOUT2_S0042": ("model release governance; evidence selection; human review", "DESCRIPTIVE", "reports_usefulness", "YES"),
    "HELDOUT2_S0043": ("consent boundary; permission boundary; privacy", "DESCRIPTIVE", "reports_usefulness", "YES"),
    "HELDOUT2_S0044": ("agent memory; source context; route provenance", "DESCRIPTIVE", "supports_retrieval", "YES"),
    "HELDOUT2_S0045": ("tool-use security; permission boundary; human review", "DESCRIPTIVE", "reports_usefulness", "YES"),
    "HELDOUT2_S0046": ("benchmark; route segment; evaluation", "DESCRIPTIVE", "reports_usefulness", "YES"),
    "HELDOUT2_S0047": ("human review; retrieval trace; evidence selection", "DESCRIPTIVE", "reports_usefulness", "YES"),
    "HELDOUT2_S0048": ("audit trail; answer support; model release governance", "DESCRIPTIVE", "reports_usefulness", "YES"),
    "HELDOUT2_S0049": ("evidence selection; source context; route segment", "DESCRIPTIVE", "supports_retrieval", "YES"),
    "HELDOUT2_S0050": ("mismatch review; policy context; claims", "DESCRIPTIVE", "reports_usefulness", "YES"),
    "HELDOUT2_S0051": ("benchmark; policy context; evaluation", "LIMITED", "warns_about", "YES"),
    "HELDOUT2_S0052": ("model release governance; AI safety evaluation; risk management", "NEGATED", "limits", "YES"),
    "HELDOUT2_S0053": ("consent boundary; permission boundary; privacy", "NEGATED", "limits", "YES"),
    "HELDOUT2_S0054": ("retrieval trace; answer support; route segment", "LIMITED", "warns_about", "YES"),
    "HELDOUT2_S0055": ("agent memory; source context; human review", "LIMITED", "warns_about", "YES"),
    "HELDOUT2_S0056": ("permission boundary; tool-use security; privacy", "NEGATED", "limits", "YES"),
    "HELDOUT2_S0057": ("human review; audit trail; evidence selection", "LIMITED", "warns_about", "YES"),
    "HELDOUT2_S0058": ("benchmark; incident response; route segment", "LIMITED", "warns_about", "YES"),
    "HELDOUT2_S0059": ("policy context; controls; risk management", "LIMITED", "warns_about", "YES"),
    "HELDOUT2_S0060": ("answer support; route segment; evidence selection", "LIMITED", "warns_about", "YES"),
    "HELDOUT2_S0061": ("benchmark; incident response; model release governance", "ACTIVE", "proposes_next_test", "YES"),
    "HELDOUT2_S0062": ("evaluation; model release governance; source context", "ACTIVE", "proposes_next_test", "YES"),
    "HELDOUT2_S0063": ("consent boundary; permission boundary; privacy", "ACTIVE", "proposes_next_test", "YES"),
    "HELDOUT2_S0064": ("retrieval trace; route provenance; route extraction", "ACTIVE", "proposes_next_test", "YES"),
    "HELDOUT2_S0065": ("agent memory; evidence selection; benchmark", "ACTIVE", "proposes_next_test", "YES"),
    "HELDOUT2_S0066": ("tool-use security; permission boundary; agent memory", "ACTIVE", "proposes_next_test", "YES"),
    "HELDOUT2_S0067": ("human review; evidence selection; answer support", "ACTIVE", "proposes_next_test", "YES"),
    "HELDOUT2_S0068": ("benchmark; gold labels; mismatch review", "ACTIVE", "proposes_next_test", "YES"),
    "HELDOUT2_S0069": ("audit trail; human review; model release governance", "ACTIVE", "proposes_next_test", "YES"),
    "HELDOUT2_S0070": ("answer support; route segment; evidence selection", "ACTIVE", "proposes_next_test", "YES"),
    "HELDOUT2_S0071": ("privacy; consent boundary; AI safety evaluation", "DESCRIPTIVE", "gives_example", "YES"),
    "HELDOUT2_S0072": ("model release governance; audit trail; human review", "DESCRIPTIVE", "gives_example", "YES"),
    "HELDOUT2_S0073": ("tool-use security; permission boundary; privacy", "DESCRIPTIVE", "gives_example", "YES"),
    "HELDOUT2_S0074": ("agent memory; source context; route provenance", "DESCRIPTIVE", "gives_example", "YES"),
    "HELDOUT2_S0075": ("privacy; answer support; evidence selection", "DESCRIPTIVE", "gives_example", "YES"),
    "HELDOUT2_S0076": ("tool-use security; permission boundary; route segment", "DESCRIPTIVE", "gives_example", "YES"),
    "HELDOUT2_S0077": ("incident response; retrieval trace; agent memory", "DESCRIPTIVE", "gives_example", "YES"),
    "HELDOUT2_S0078": ("benchmark; human review; route segment", "DESCRIPTIVE", "gives_example", "YES"),
    "HELDOUT2_S0079": ("audit trail; evidence selection; model release governance", "DESCRIPTIVE", "gives_example", "YES"),
    "HELDOUT2_S0080": ("answer support; policy context; route segment", "DESCRIPTIVE", "gives_example", "YES"),
}


def main():
    with IN_PATH.open("r", encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))

    for row in rows:
        entities, status, relation, answer_relevant = GOLD_FIELDS[row["segment_id"]]
        row["gold_entities"] = entities
        row["gold_operative_status"] = status
        row["gold_relation"] = relation
        row["gold_answer_relevant"] = answer_relevant

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with OUT_PATH.open("w", encoding="utf-8", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows([{field: row.get(field, "") for field in FIELDNAMES} for row in rows])

    print(f"Rows written: {len(rows)}")
    print(f"Wrote: {OUT_PATH}")


if __name__ == "__main__":
    main()
