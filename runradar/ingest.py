# -*- coding: utf-8 -*-
# code: language=python tabSize=4
#
from pathlib import Path

import yaml
from blessed import Terminal

from .model import Blip
from .model import Quadrant
from .model import Radar
from .model import Ring


term = Terminal()


class Ingester:
    def __init__(self, path: Path) -> None:
        self.radar_path = path
        print(f"Radar path: {path.absolute()}")

    def parse_blip(self, quadrant: Quadrant, ring: Ring, path: Path) -> Blip:
        print(f"Processing: {path}{term.clear_eol()}\r", end="", flush=True)
        with open(path) as blip_file:
            blip_spec = yaml.safe_load(blip_file)

            blip = Blip(
                quadrant=quadrant.name,
                ring=ring.name,
                **{k: v for k, v in blip_spec["blip"].items() if k != "is_new"},
            )
            if "is_new" in blip_spec["blip"]:
                blip.previous_ring = None if blip_spec["blip"]["is_new"] else blip.ring
            else:
                blip.previous_ring = blip.ring
            return blip

    def ingest(self) -> Radar:
        if (self.radar_path / "specs.yml").exists():
            file = self.radar_path / "specs.yml"
        else:
            file = self.radar_path / "specs.yaml"

        with open(file) as f:
            specs = yaml.safe_load(f)

        rings = [Ring(**r) for r in specs["rings"]]
        quadrants = [Quadrant(**q) for q in specs["quadrants"]]
        print(f"Rings: {', '.join(r.name for r in rings)}")
        print(f"Quadrants: {', '.join(q.name for q in quadrants)}")

        radar = Radar(rings, quadrants)
        count = 0

        for ring in rings:
            for quadrant in quadrants:
                blips_dir: Path = self.radar_path / quadrant.id / ring.id
                if not blips_dir.exists():
                    continue
                if not blips_dir.is_dir():
                    raise OSError(f"Path {blips_dir} must be a directory")

                for path in blips_dir.iterdir():
                    if path.as_posix().endswith((".yaml", ".yml")):
                        blip = self.parse_blip(quadrant, ring, path)
                        radar.add_blip(blip)
                        count = count + 1
        print(f"Processed: {count:2} blips{term.clear_eol()}")

        return radar
