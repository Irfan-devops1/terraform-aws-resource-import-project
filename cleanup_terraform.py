
import re
import shutil
from datetime import datetime
from pathlib import Path


FILE = Path("temp_generated.tf")
BACKUP_DIR = Path("terraform_backups")


def count_braces(line):
    line = re.sub(r'"(?:\\.|[^"\\])*"', '""', line)
    line = line.split("#", 1)[0]
    line = line.split("//", 1)[0]
    return line.count("{") - line.count("}")


def remove_old_backups():
    """Remove old backup TF files from the project root."""

    patterns = [
        "generated_resources_backup_*.tf",
    ]

    removed = 0

    for pattern in patterns:
        for backup in Path(".").glob(pattern):
            if backup.is_file():
                backup.unlink()
                print(f"Removed old backup: {backup.name}")
                removed += 1

    if removed == 0:
        print("No old backup files found in project directory.")


def get_resource_blocks(lines):
    blocks = []
    i = 0

    while i < len(lines):
        if re.match(
            r'^\s*resource\s+"aws_instance"\s+"[^"]+"\s*\{',
            lines[i]
        ):
            start = i
            depth = 0

            while i < len(lines):
                depth += count_braces(lines[i])

                if depth == 0:
                    blocks.append((start, i))
                    break

                i += 1

        i += 1

    return blocks


def clean_instance(block):
    depth = 0
    attributes = set()
    primary_eni = False

    for line in block:
        stripped = line.strip()

        if depth == 1:
            match = re.match(
                r"^([A-Za-z_][A-Za-z0-9_]*)\s*=",
                stripped
            )

            if match:
                attributes.add(match.group(1))

            if re.match(
                r"^primary_network_interface\s*\{",
                stripped
            ):
                primary_eni = True

        depth += count_braces(line)

    remove_attributes = set()

    if primary_eni:
        remove_attributes.update({
            "associate_public_ip_address",
            "private_ip",
            "secondary_private_ips",
            "ipv6_address_count",
            "ipv6_addresses",
            "subnet_id",
            "vpc_security_group_ids",
            "security_groups",
            "source_dest_check",
        })

    else:
        if (
            "ipv6_address_count" in attributes
            and "ipv6_addresses" in attributes
        ):
            ipv6_count = None
            ipv6_addresses = None

            for line in block:
                count_match = re.match(
                    r"^\s*ipv6_address_count\s*=\s*(\d+)",
                    line
                )

                address_match = re.match(
                    r"^\s*ipv6_addresses\s*=\s*(.*)",
                    line
                )

                if count_match:
                    ipv6_count = int(count_match.group(1))

                if address_match:
                    ipv6_addresses = address_match.group(1).strip()

            if ipv6_count == 0 and ipv6_addresses == "[]":
                remove_attributes.add("ipv6_address_count")

            elif ipv6_count == 0:
                remove_attributes.add("ipv6_address_count")

            elif ipv6_addresses == "[]":
                remove_attributes.add("ipv6_addresses")

            else:
                print(
                    "WARNING: IPv6 arguments need manual review."
                )

        if (
            "security_groups" in attributes
            and "vpc_security_group_ids" in attributes
        ):
            remove_attributes.add("security_groups")

    if not remove_attributes:
        return block, 0

    cleaned = []
    depth = 0
    removed = 0

    for line in block:
        stripped = line.strip()

        if depth == 1:
            match = re.match(
                r"^([A-Za-z_][A-Za-z0-9_]*)\s*=",
                stripped
            )

            if match and match.group(1) in remove_attributes:
                removed += 1
                depth += count_braces(line)
                continue

        cleaned.append(line)
        depth += count_braces(line)

    return cleaned, removed


def main():

    if not FILE.exists():
        print(f"ERROR: {FILE} not found.")
        return

    # Remove old backups from the project root.
    remove_old_backups()

    original_lines = FILE.read_text(
        encoding="utf-8"
    ).splitlines(keepends=True)

    blocks = get_resource_blocks(original_lines)

    if not blocks:
        print("No aws_instance resources found.")
        return

    updated_lines = original_lines[:]

    total_checked = 0
    total_removed = 0

    for start, end in reversed(blocks):
        block = updated_lines[start:end + 1]

        cleaned, removed = clean_instance(block)

        updated_lines[start:end + 1] = cleaned

        total_checked += 1
        total_removed += removed

    if total_removed:

        # Store backups outside the Terraform root.
        BACKUP_DIR.mkdir(exist_ok=True)

        backup = BACKUP_DIR / (
            f"generated_resources_backup_"
            f"{datetime.now():%Y%m%d_%H%M%S}.tf"
        )

        shutil.copy2(FILE, backup)

        FILE.write_text(
            "".join(updated_lines),
            encoding="utf-8"
        )

        print(f"Removed {total_removed} conflicting arguments.")
        print(f"Backup saved outside Terraform root: {backup}")

    else:
        print("No changes required.")

    print(f"EC2 resources checked: {total_checked}")


if __name__ == "__main__":
    main()
