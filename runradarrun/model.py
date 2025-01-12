# -*- coding: utf-8 -*-
# code: language=python tabSize=4
#
import argparse
import webbrowser
from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union


OptionalStrOrListStr = Optional[Union[str, List[str]]]


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

    def __init__(self, rings: List[Ring], quadrants: List[Quadrant]) -> None:
        if Radar.MIN_NUM_RINGS <= len(rings) <= Radar.MAX_NUM_RINGS:
            self.rings = rings
        else:
            raise ValueError(
                f"Radar must have between {Radar.MIN_NUM_RINGS} and {Radar.MAX_NUM_RINGS}: {rings}"
            )

        if len(quadrants) != 4:
            raise ValueError(f"Radar must have 4 quadrants: {quadrants}")
        self.quadrants = quadrants
        self._blips = []

    def add_blip(self, blip: Blip) -> None:
        self._blips.append(blip)

    @property
    def blips(self) -> Tuple[Blip]:
        return tuple(self._blips)


class RadarPresentation(ABC):
    def __init__(self, radar: Radar) -> None:
        self.radar = radar

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def serialize(self) -> str:
        pass


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
