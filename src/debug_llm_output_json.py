import argparse

from llm_output_parsing import extract_json_object_from_text
from llm_output_utils import parse_extraction, read_jsonl


def preview(value, limit=500):
    return str(value or "").replace("\n", "\\n")[:limit]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--outputs", required=True)
    args = parser.parse_args()

    rows = read_jsonl(args.outputs)
    found_count = 0
    valid_count = 0
    for line_number, record, line_error in rows:
        if line_error:
            print(f"line={line_number}")
            print(f"parse_error={line_error}")
            continue
        raw = record.get("raw_response", "")
        found, parse_error = extract_json_object_from_text(raw) if raw else (record.get("extraction"), "")
        extraction, valid, errors = parse_extraction(record)
        found_count += int(found is not None)
        valid_count += int(valid)
        print(f"line={line_number}")
        print(f"segment_id={record.get('segment_id', '')}")
        print(f"provider={record.get('provider', '')}")
        print(f"model={record.get('model', '')}")
        print(f"top_level_keys={','.join(sorted(record.keys()))}")
        print(f"raw_response_exists={'YES' if 'raw_response' in record else 'NO'}")
        print(f"raw_response_preview={preview(raw)}")
        print(f"json_object_found={'YES' if found is not None else 'NO'}")
        print(f"parsed_keys={','.join(sorted(found.keys())) if isinstance(found, dict) else ''}")
        if parse_error:
            print(f"json_object_error={parse_error}")
        print(f"validation={'VALID' if valid else 'INVALID'}")
        print(f"errors={'; '.join(errors)}")
        print(f"normalized_role={extraction.get('role', '')}")
        print("")
    print(f"rows={len(rows)}")
    print(f"json_object_found_count={found_count}")
    print(f"valid_count={valid_count}")


if __name__ == "__main__":
    main()
