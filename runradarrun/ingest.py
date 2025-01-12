# -*- coding: utf-8 -*-
# code: language=python tabSize=4
#
import argparse
from pathlib import Path
from typing import Optional

import yaml

from .model import Blip
from .model import Quadrant
from .model import Radar
from .model import RadarException
from .model import Ring
from .output import Printer


class Ingester:
    def __init__(
        self, path: Path, options: Optional[argparse.Namespace] = None
    ) -> None:
        self.radar_path = path
        self.options = options
        self.printer = Printer(options.quiet)

    def parse_blip(self, quadrant: Quadrant, ring: Ring, path: Path) -> Blip:
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

        rings = {pos: Ring(**r) for pos, r in specs["rings"].items()}
        quadrants = {pos: Quadrant(**q) for pos, q in specs["quadrants"].items()}
        radar = Radar(rings, quadrants)
        count = 0

        for ring in rings.values():
            for quadrant in quadrants.values():
                blips_dir: Path = self.radar_path / quadrant.id / ring.id
                if not blips_dir.exists():
                    continue
                if not blips_dir.is_dir():
                    raise RadarException(f"Path {blips_dir} must be a directory")

                for path in blips_dir.iterdir():
                    if path.as_posix().endswith((".yaml", ".yml")):
                        blip = self.parse_blip(quadrant, ring, path)
                        radar.add_blip(blip)
                        count = count + 1

        return radar
