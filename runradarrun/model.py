# -*- coding: utf-8 -*-
# code: language=python tabSize=4
#
import argparse
import webbrowser
from dataclasses import dataclass
from pathlib import Path
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union


OptionalStrOrListStr = Optional[Union[str, List[str]]]


class RadarException(Exception):
    pass


@dataclass
class Ring:
    id: str
    name: str


@dataclass
class Quadrant:
    id: str
    name: str


class Blip:
    def __init__(
        self,
        name: str,
        ring: str,
        quadrant: str,
        previous_ring: Optional[str] = None,
        description: OptionalStrOrListStr = None,
        references: OptionalStrOrListStr = None,
        tags: OptionalStrOrListStr = None,
    ) -> None:
        self.name = name
        self.ring = ring
        self.quadrant = quadrant
        self.previous_ring = previous_ring
        self.description = description or []
        self.references = references or []
        self.tags = tags or []

    @property
    def is_new(self) -> bool:
        return self.previous_ring is None

    def __str__(self) -> str:
        return f"Blip({self.name}, r={self.ring}, q={self.quadrant}{' NEW' if self.is_new else ''})"

    __repr__ = __str__


class Radar:
    MIN_NUM_RINGS = 3
    MAX_NUM_RINGS = 4

    Q_TL = "top_left"
    Q_TR = "top_right"
    Q_BL = "bottom_left"
    Q_BR = "bottom_right"

    QUADRANTS_CLOCKWISE = (Q_TL, Q_TR, Q_BR, Q_BL)
    QUADRANTS_CTR_CLOCKWISE = (Q_TL, Q_BL, Q_BR, Q_TR)
    QUADRANTS_TL_BL_TR_BR = (Q_TL, Q_BL, Q_TR, Q_BR)
    QUADRANTS_TL_TR_BL_BR = (Q_TL, Q_TR, Q_BL, Q_BR)

    def __init__(self, rings: Dict[str, Ring], quadrants: Dict[str, Quadrant]) -> None:
        if Radar.MIN_NUM_RINGS <= len(rings) <= Radar.MAX_NUM_RINGS:
            self._rings = rings
        else:
            raise RadarException(
                f"Radar must have between {Radar.MIN_NUM_RINGS} and {Radar.MAX_NUM_RINGS}: {rings}"
            )

        if len(quadrants) != 4:
            raise RadarException(f"Radar must have 4 quadrants: {quadrants}")
        self._quadrants = quadrants
        self._blips = []

    def add_blip(self, blip: Blip) -> None:
        self._blips.append(blip)

    @property
    def blips(self) -> Tuple[Blip]:
        return tuple(self._blips)

    @property
    def rings_raw(self):
        return self._rings

    @property
    def quadrants_raw(self):
        return self._quadrants

    def rings_outward(self) -> List[Ring]:
        return [
            self._rings[ring]
            for ring in ["inner", "mid_inner", "mid_outer", "outer"]
            if self._rings.get(ring)
        ]

    def rings_inward(self) -> List[Ring]:
        return [
            self._rings[ring]
            for ring in ["outer", "mid_outer", "mid_inner", "inner"]
            if self._rings.get(ring)
        ]

    def quadrants(self, order: Tuple) -> List[Quadrant]:
        return [self._quadrants[q] for q in order]


class AbstractPublisher:
    publishing_url = None

    def __init__(
        self, radar: Radar, options: Optional[argparse.Namespace] = None
    ) -> None:
        self.radar = radar
        self.options = options
        self._output = None

    def make_output(self) -> str:
        raise NotImplementedError()

    @classmethod
    def cli_id(cls):
        raise NotImplementedError()

    @property
    def output(self) -> str:
        if self._output is None:
            self._output = self.make_output()
        return self._output

    def run(self):
        # optional implementation
        pass

    def cleanup(self):
        # optional implementation
        pass

    @property
    def url(self) -> str:
        if self.publishing_url is None:
            raise NotImplementedError()
        return self.publishing_url

    def write(self, output: Path) -> None:
        with open(output, "w") as outputfile:
            outputfile.write(self.output)

    def open_url(self, url: Optional[str] = None) -> None:
        if not url:
            url = self.url
        if not self.options.run_only:
            webbrowser.open(url, new=1)
