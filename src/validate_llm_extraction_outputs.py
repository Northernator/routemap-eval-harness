import argparse
from collections import Counter
from pathlib import Path

from llm_output_utils import parse_extraction, read_jsonl, rows_by_segment


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--requests", required=True)
    parser.add_argument("--outputs", required=True)
    parser.add_argument("--report", required=True)
    args = parser.parse_args()

    request_rows = read_jsonl(args.requests)
    output_rows = read_jsonl(args.outputs)
    requests, request_errors = rows_by_segment(request_rows)
    outputs, output_errors = rows_by_segment(output_rows)
    missing = sorted(set(requests) - set(outputs))
    unknown = sorted(set(outputs) - set(requests))
    matched = sorted(set(requests) & set(outputs))
    validation_errors = []
    valid_count = 0
    provider_error_count = 0
    invalid_schema_count = 0

    for segment_id in matched:
        line_number, record = outputs[segment_id]
        _, valid, errors = parse_extraction(record)
        if valid:
            valid_count += 1
        else:
            if "provider_error_like_output" in errors:
                provider_error_count += 1
            else:
                invalid_schema_count += 1
            validation_errors.append((segment_id, line_number, errors))
    invalid_count = len(validation_errors) + len(output_errors)
    counts = Counter(error for _, _, errors in validation_errors for error in errors)

    lines = [
        "# LLM Output Validation",
        "",
        f"- Request count: {len(requests)}",
        f"- Output count: {len(outputs)}",
        f"- Matched count: {len(matched)}",
        f"- Missing outputs: {len(missing)}",
        f"- Unknown segment IDs: {len(unknown)}",
        f"- Valid outputs: {valid_count}",
        f"- Invalid extraction schema: {invalid_schema_count}",
        f"- Provider/error outputs: {provider_error_count}",
        f"- Invalid outputs: {invalid_count}",
        "",
        "## Missing Outputs",
        "",
    ]
    lines.extend(f"- {segment_id}" for segment_id in missing[:50])
    lines.extend(["", "## Unknown Segment IDs", ""])
    lines.extend(f"- {segment_id}" for segment_id in unknown[:50])
    lines.extend(["", "## Validation Errors By Row", ""])
    for segment_id, line_number, errors in validation_errors:
        lines.append(f"- {segment_id} line {line_number}: {'; '.join(errors)}")
    for line_number, segment_id, error in request_errors + output_errors:
        lines.append(f"- line {line_number}: {error}")
    lines.extend(["", "## Error Counts", "", "| error | count |", "|---|---:|"])
    for error, count in counts.most_common():
        lines.append(f"| {error} | {count} |")
    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines), encoding="utf-8")

    print(f"Request count: {len(requests)}")
    print(f"Output count: {len(outputs)}")
    print(f"Matched count: {len(matched)}")
    print(f"Missing outputs: {len(missing)}")
    print(f"Unknown segment IDs: {len(unknown)}")
    print(f"Valid outputs: {valid_count}")
    print(f"Invalid extraction schema: {invalid_schema_count}")
    print(f"Provider/error outputs: {provider_error_count}")
    print(f"Invalid outputs: {invalid_count}")
    print(f"Report: {report}")


if __name__ == "__main__":
    main()
