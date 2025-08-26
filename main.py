import argparse
import os
import random
import re
import shutil
from typing import Optional

import pysubs2
from pysubs2 import Alignment, SSAFile

import resample_resolution


def tag_with_slash(tag: str) -> str:
    # make sure it always starts with a backslash
    return "\\" + tag.lstrip("\\")


def transfer_signs(source_subs: SSAFile, target_subs: SSAFile, extra_excluded_tags: Optional[list[str]] = None):
    # Step 1: Collect used style names from source events
    used_style_names = set(event.style for event in source_subs.events if hasattr(event, "style"))

    # Step 2: Copy only used styles from source to target
    for name in used_style_names:
        if name in source_subs.styles:
            if name not in target_subs.styles:
                target_subs.styles[name] = source_subs.styles[name]
            else:
                # If the style already exists in the target, randomly rename it
                # to avoid overwriting it
                attampts = 0
                while True:
                    try:
                        if attampts > 20:
                            raise Exception("Failed to rename style")
                        random_name = f"{name}_{str(random.randint(1000, 9999))}"
                        source_subs.rename_style(name, random_name)
                        break
                    except Exception as e:
                        attampts += 1
                        continue
                target_subs.styles[random_name] = source_subs.styles[random_name]

    transfer_sign_events(source_subs, target_subs, extra_excluded_tags)

    # Step 3: Remove unused styles from the target
    # (after combining, in case there were already styles)
    final_used_styles = set(event.style for event in target_subs.events if hasattr(event, "style"))
    target_subs.styles = {name: style for name, style in target_subs.styles.items() if name in final_used_styles}


def transfer_sign_events(source_subs: SSAFile, target_subs: SSAFile, extra_excluded_tags: Optional[list[str]] = None):
    # Copy only events whose style name contains "sign" (case-insensitive)
    excluded_prefixes = ("\\N", "\\be", "\\fe", "\\r", "\\b", "\\bord", "\\q", "\\u", "\\s")

    # Add extra excluded tags
    if extra_excluded_tags is not None:
        excluded_prefixes += tuple(extra_excluded_tags)
    # Unique tuples
    excluded_prefixes = tuple(dict.fromkeys(excluded_prefixes))

    added_events = []

    sign_events = [
        event
        for event in source_subs.events
        if not event.is_comment and event not in added_events and ("sign" in event.style.lower())
    ]
    if len(sign_events) > 0:
        sign_start_marker = pysubs2.SSAEvent(start=0, end=0, text="SIGN", type="Comment")
        target_subs.events.append(sign_start_marker)
        # Append to target events
        target_subs.events.extend(sign_events)
        added_events.extend(sign_events)

    special_tags_events = [
        event
        for event in source_subs.events
        if not event.is_comment
        and event not in added_events
        and (
            "".join(
                tag
                for block in re.findall(r"{[^}]*}", event.text)
                for tag in re.findall(r"\\[a-zA-Z]+\(?[^\\}]*\)?", block)
                if not any(tag.startswith(prefix) for prefix in excluded_prefixes)
            )
        )
    ]
    if len(special_tags_events) > 0:
        special_alignment_marker = pysubs2.SSAEvent(start=0, end=0, text="Lines with special Tags", type="Comment")
        target_subs.events.append(special_alignment_marker)
        # Append to target events
        target_subs.events.extend(special_tags_events)
        added_events.extend(special_tags_events)

    special_alignment_styles = [
        style_name for style_name, style in source_subs.styles.items() if style.alignment != Alignment.BOTTOM_CENTER
    ]

    special_alignment_events = [
        event
        for event in source_subs.events
        if not event.is_comment and event not in added_events and event.style in special_alignment_styles
    ]
    if len(special_alignment_events) > 0:
        special_alignment_marker = pysubs2.SSAEvent(start=0, end=0, text="Lines with unusual Alignment", type="Comment")
        target_subs.events.append(special_alignment_marker)
        # Append to target events
        target_subs.events.extend(special_alignment_events)
        added_events.extend(special_alignment_events)

    special_margin_styles = [
        style_name
        for style_name, style in source_subs.styles.items()
        if style.marginl > 300 or style.marginr > 300 or style.marginv > 300
    ]

    special_margin_events = [
        event
        for event in source_subs.events
        if not event.is_comment
        and event not in added_events
        and (event.style in special_margin_styles or event.marginl != 0 or event.marginr != 0 or event.marginv != 0)
    ]

    if len(special_margin_events) > 0:
        special_margin_marker = pysubs2.SSAEvent(start=0, end=0, text="Lines with unusual Margin", type="Comment")
        target_subs.events.append(special_margin_marker)
        # Append to target events
        target_subs.events.extend(special_margin_events)
        added_events.extend(special_margin_events)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Transfer signs from one .ass subtitle file(s) to another.")
    parser.add_argument("source", help="Path to the source .ass file or source directory.")
    parser.add_argument("target", help="Path to the target .ass file or target directory.")
    parser.add_argument(
        "-a",
        "--aegisubcli",
        dest="aegisubcli",
        help="Path to the aegisub-cli tool. Defaults to searching for aegisub-cli in the PATH environment variable.",
    )
    parser.add_argument(
        "-s",
        "--skip-tags",
        dest="extra_excluded_tags",
        nargs="*",
        type=tag_with_slash,
        default=[],
        help=".ASS extra tags to skip (without backslash). These tags will be 'skipped' before checking whether the line has special tags or not. Example: skip \\i (italic) or \\pos tags lines '-s pos i' these tags will add to the default skipped tags (\\N \\be \\fe \\r \\b \\bord \\q \\u \\s).",
    )

    args = parser.parse_args()

    source_path = args.source
    target_path = args.target
    aegisubcli = args.aegisubcli
    extra_excluded_tags = args.extra_excluded_tags

    # Check if inputs are files or directories
    source_is_dir = os.path.isdir(source_path)
    target_is_dir = os.path.isdir(target_path)

    # Validate input types
    if source_is_dir != target_is_dir:
        print("❌ Error: Both source and target must be either files or directories.")
        exit(1)

    if not source_is_dir and not os.path.isfile(source_path):
        print(f"❌ Error: Source file not found at {source_path}")
        exit(1)

    if not target_is_dir and not os.path.isfile(target_path):
        print(f"❌ Error: Target file not found at {target_path}")
        exit(1)

    if not source_is_dir:
        # Case 1: Single file pair
        print(f"Processing single file pair: {source_path} -> {target_path}")
        try:
            source_subs = pysubs2.load(source_path)
            target_subs = pysubs2.load(target_path)

            # Resolution check for single file
            source_playresx = source_subs.info.get("PlayResX", 0)
            source_playresy = source_subs.info.get("PlayResY", 0)
            target_playresx = target_subs.info.get("PlayResX", 1)
            target_playresy = target_subs.info.get("PlayResY", 1)

            if target_playresx == 1 or target_playresy == 1:
                print("❌ Error: target file must have PlayResX and PlayResY")
                exit(1)

            if source_playresx != target_playresx or source_playresy != target_playresy:
                if aegisubcli or shutil.which("aegisub-cli"):
                    if aegisubcli or shutil.which("aegisub-cli"):
                        if aegisubcli and not os.path.exists(aegisubcli):
                            print(f"❌ Error: aegisub-cli not found at {aegisubcli}")
                            exit(1)

                    print(
                        f"🔁 Info: PlayResX and PlayResY differ. Resampling subtitles to target resolution {target_playresx}x{target_playresy}..."
                    )
                    resample_resolution_args = [
                        source_path,
                        "-v",
                        f"{target_playresx}x{target_playresy}",
                        "-a",
                        aegisubcli or "aegisub-cli",
                    ]
                    resample_resolution.main(resample_resolution_args)
                else:
                    print(
                        f"""❌ Error: PlayResX and PlayResY differ and aegisub-cli not found in PATH. Use -a /path/to/aegisub-cli to continue.
                            Or use aegisub, subtitleedit to change subtitle resolution manually.
                        """
                    )
                    exit(1)

            # Perform sign transfer
            transfer_signs(source_subs, target_subs, extra_excluded_tags)

            # Overwrite target file
            target_subs.save(target_path)
            print("✅ Sign transfer complete for single file pair.")

        except pysubs2.exceptions.Pysubs2Error as e:
            print(f"❌ Error processing files: {e}")
            exit(1)
        except Exception as e:
            print(f"❌ An unexpected error occurred: {e}")
            exit(1)

    else:
        # Case 2: Directory pair
        print(f"Processing directory pair: {source_path} -> {target_path}")

        # Get list of .ass files in both directories
        source_files = {f: os.path.join(source_path, f) for f in os.listdir(source_path) if f.endswith(".ass")}
        target_files = {f: os.path.join(target_path, f) for f in os.listdir(target_path) if f.endswith(".ass")}

        processed_count = 0
        skipped_count = 0

        # Iterate through source files and find corresponding target files
        for filename, full_source_path in source_files.items():
            if filename in target_files:
                full_target_path = target_files[filename]
                print(f"Processing file pair: {filename} ({full_source_path} -> {full_target_path})")
                try:
                    source_subs = pysubs2.load(full_source_path)
                    target_subs = pysubs2.load(full_target_path)

                    # Resolution check for current file pair
                    source_playresx = source_subs.info.get("PlayResX", 0)
                    source_playresy = source_subs.info.get("PlayResY", 0)
                    target_playresx = target_subs.info.get("PlayResX", 1)  # Default to 1
                    target_playresy = target_subs.info.get("PlayResY", 1)  # Default to 1

                    if target_playresx == 1 or target_playresy == 1:
                        print("❌ Error: target file must have PlayResX and PlayResY")
                        skipped_count += 1
                        continue  # Skip to the next file pair
                    if source_playresx != target_playresx or source_playresy != target_playresy:
                        if aegisubcli or shutil.which("aegisub-cli"):
                            if aegisubcli and not os.path.exists(aegisubcli):
                                print(f"❌ Error: aegisub-cli not found at {aegisubcli}")
                                exit(1)
                            print(
                                f"🔁 Info: PlayResX and PlayResY differ for {filename}. Resampling subtitles to target resolution {target_playresx}x{target_playresy}..."
                            )
                            resample_resolution_args = [
                                full_source_path,
                                "-v",
                                f"{target_playresx}x{target_playresy}",
                                "-a",
                                aegisubcli or "aegisub-cli",
                            ]
                            resample_resolution.main(resample_resolution_args)
                        else:
                            skipped_count += 1
                            print(
                                f"""❌ Error: PlayResX and PlayResY differ for {filename} and aegisub-cli not found in PATH. Skipping this pair.
                                              Use -a /path/to/aegisub-cli or aegisub, subtitleedit to change subtitle resolution manually.
                                """
                            )
                            continue  # Skip to the next file pair

                    # Perform sign transfer
                    transfer_signs(source_subs, target_subs, extra_excluded_tags)

                    # Overwrite target file
                    target_subs.save(full_target_path)
                    print(f"✅ Sign transfer complete for {filename}.")
                    processed_count += 1

                except pysubs2.exceptions.Pysubs2Error as e:
                    print(f"❌ Error processing {filename}: {e}. Skipping.")
                    skipped_count += 1
                    continue
                except Exception as e:
                    print(f"❌Error: An unexpected error occurred processing {filename}: {e}. Skipping.")
                    skipped_count += 1
                    continue
            else:
                print(f"⚠️ Warning: Corresponding target file not found for {filename} in {target_path}. Skipping.")
                skipped_count += 1

        print("\n--- Summary ---")
        print(f"✅ Processed {processed_count} file pair(s).")
        print(f"⚠️ Skipped {skipped_count} file pair(s).")
