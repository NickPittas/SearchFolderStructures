import os
import json
import argparse

def scan_folder_structure(root_path):
    """
    Recursively scan the folder structure starting from root_path.
    Returns a nested dict representing the folder structure.
    """
    structure = {}
    for entry in os.scandir(root_path):
        if entry.is_dir():
            structure[entry.name] = scan_folder_structure(entry.path)
        elif entry.is_file():
            if '__files__' not in structure:
                structure['__files__'] = []
            structure['__files__'].append(entry.name)
    return structure

def main():
    parser = argparse.ArgumentParser(description="Scan a folder and output its structure as JSON.")
    parser.add_argument('folder', help='Path to the folder to scan')
    parser.add_argument('-o', '--output', help='Output JSON file (default: print to stdout)')
    args = parser.parse_args()

    folder = os.path.abspath(args.folder)
    if not os.path.isdir(folder):
        print(f"Error: {folder} is not a valid directory.")
        return

    structure = scan_folder_structure(folder)
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(structure, f, indent=2, ensure_ascii=False)
        print(f"Folder structure saved to {args.output}")
    else:
        print(json.dumps(structure, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
