from json import load
from pathlib import Path
from typing import Dict

def parse(map: Path) -> Dict:
    parsed_json_map = load(map)
    return parsed_json_map

with Path('./schema/sample.json').open() as map_file:
    result = parse(map_file)
    print()