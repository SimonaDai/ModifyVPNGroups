import argparse
import re
import sys
from pathlib import Path


def parse_proxy_names(proxies_block: str):
    names = []
    # Regex captures either single-quoted, double-quoted, or unquoted value until comma or brace
    pattern = re.compile(r"name:\s*(?:'([^']*)'|\"([^\"]*)\"|([^,}\n]+))")
    for line in proxies_block.splitlines():
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        m = pattern.search(s)
        if m:
            name_val = m.group(1) or m.group(2) or m.group(3)
            if name_val is None:
                continue
            name_val = name_val.strip()
            names.append(name_val)
    return names


def wrap_yaml_name(name: str) -> str:
    # Escape single quotes by doubling them and wrap with single quotes
    escaped = name.replace("'", "''")
    return f"'{escaped}'"


def generate_groups(names, chunk_size=8, group_prefix="节点分组"):
    groups = [names[i : i + chunk_size] for i in range(0, len(names), chunk_size)]
    out_lines = []
    out_lines.append("proxy-groups:")
    for i, group in enumerate(groups):
        group_name = f"{group_prefix} {i+1}"
        proxies_str = ", ".join(wrap_yaml_name(n) for n in group)
        out_lines.append(f"    - {{ name: {wrap_yaml_name(group_name)}, type: select, proxies: [{proxies_str}] }}")
    return "\n".join(out_lines)


def main():
    # keke.yaml 换成自己的 Clash 配置文件路径
    parser = argparse.ArgumentParser(description="Generate proxy-groups from proxies list in a Clash YAML file")
    parser.add_argument("-i", "--input", default=str(Path(__file__).parent / "keke.yaml"), help="input YAML file path")
    parser.add_argument(
        "-o", "--output", default=str(Path(__file__).parent / "generated_proxy_groups.txt"), help="output TXT file path"
    )
    parser.add_argument("-c", "--chunk", type=int, default=8, help="number of proxies per group")
    parser.add_argument("--prefix", default="节点分组", help="group name prefix")
    args = parser.parse_args()

    try:
        with open(args.input, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file: {e}")
        sys.exit(1)

    start_marker = "proxies:"
    end_marker = "proxy-groups:"
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx == -1:
        print("Could not find 'proxies:' section in input file")
        sys.exit(1)

    # If proxy-groups not present, parse until end of file
    if end_idx == -1:
        proxies_block = content[start_idx + len(start_marker) :]
    else:
        proxies_block = content[start_idx + len(start_marker) : end_idx]

    names = parse_proxy_names(proxies_block)
    if not names:
        print("No proxy names parsed from input file")
        sys.exit(1)

    out_text = generate_groups(names, chunk_size=args.chunk, group_prefix=args.prefix)

    try:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out_text)
    except Exception as e:
        print(f"Error writing output file: {e}")
        sys.exit(1)

    print(f"Generated proxy-groups written to: {args.output}")


if __name__ == "__main__":
    main()
