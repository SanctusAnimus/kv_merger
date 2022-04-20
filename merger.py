from os import walk, path
from pathlib import Path


def merge_profile(profile: dict):
    cwd = Path.cwd()
    if not profile["source_dir"]:
        return
    if not profile["target_file_name"]:
        return
    src = cwd / profile["source_dir"]
    target = cwd / profile["target_file_name"]
    if not src.exists():
        # print("source in merge does not exist")
        return
    if not target.exists():
        # print("target in merge does not exist")
        return
    read_content = [profile["prefix"], ]
    for root, dirs, files in walk(src):
        for file_name in files:
            open_path = path.join(root, file_name)
            with open(open_path, 'r') as src:
                content = src.read().strip()
                read_content.append(
                    f"//--------------------------------------------------------------------\n"
                    f"// START  - {file_name} - START\n"
                    f"//--------------------------------------------------------------------\n"
                    f"{content}\n"
                    f"//--------------------------------------------------------------------\n"
                    f"// END - {file_name} - END\n"
                    f"//--------------------------------------------------------------------\n\n"
                )
    read_content.append(f"\n{profile['postfix']}\n\n")
    with open(target, "w") as target_file:
        target_file.writelines(read_content)
