import argparse

import pytest
import yaml

from runradarrun.ingest import Ingester
from runradarrun.model import Quadrant, Ring

SPECS = {
    "rings": {
        "inner": {"id": "adopt", "name": "Adopt"},
        "mid_inner": {"id": "trial", "name": "Trial"},
        "mid_outer": {"id": "assess", "name": "Assess"},
        "outer": {"id": "hold", "name": "Hold"},
    },
    "quadrants": {
        "top_left": {"id": "strat", "name": "Strategies"},
        "top_right": {"id": "tools", "name": "Tools"},
        "bottom_left": {"id": "techniques", "name": "Techniques"},
        "bottom_right": {"id": "lang", "name": "Languages"},
    },
}


@pytest.fixture
def options():
    return argparse.Namespace(quiet=True)


@pytest.fixture
def radar_dir(tmp_path):
    (tmp_path / "specs.yaml").write_text(yaml.dump(SPECS))
    return tmp_path


@pytest.fixture
def ingester(radar_dir, options):
    return Ingester(radar_dir, options=options)


class TestParseBlip:
    def test_basic(self, ingester, tmp_path):
        blip_file = tmp_path / "docker.yaml"
        blip_file.write_text(yaml.dump({"blip": {"name": "Docker", "description": "Containers"}}))
        quadrant = Quadrant(id="tools", name="Tools")
        ring = Ring(id="adopt", name="Adopt")

        blip = ingester.parse_blip(quadrant, ring, blip_file)

        assert blip.name == "Docker"
        assert blip.ring == "Adopt"
        assert blip.quadrant == "Tools"
        assert blip.description == "Containers"

    def test_is_new_explicit_true(self, ingester, tmp_path):
        blip_file = tmp_path / "new.yaml"
        blip_file.write_text(yaml.dump({"blip": {"name": "X", "is_new": True}}))
        blip = ingester.parse_blip(Quadrant(id="q", name="Q"), Ring(id="r", name="R"), blip_file)
        assert blip.is_new is True

    def test_is_new_explicit_false(self, ingester, tmp_path):
        blip_file = tmp_path / "old.yaml"
        blip_file.write_text(yaml.dump({"blip": {"name": "X", "is_new": False}}))
        blip = ingester.parse_blip(Quadrant(id="q", name="Q"), Ring(id="r", name="R"), blip_file)
        assert blip.is_new is False

    def test_is_new_omitted_defaults_to_not_new(self, ingester, tmp_path):
        blip_file = tmp_path / "no_flag.yaml"
        blip_file.write_text(yaml.dump({"blip": {"name": "X"}}))
        blip = ingester.parse_blip(Quadrant(id="q", name="Q"), Ring(id="r", name="R"), blip_file)
        assert blip.is_new is False


class TestIngest:
    def test_empty_radar(self, radar_dir, options):
        radar = Ingester(radar_dir, options=options).ingest()
        assert len(radar.blips) == 0

    def test_blips_loaded(self, radar_dir, options):
        blip_dir = radar_dir / "tools" / "adopt"
        blip_dir.mkdir(parents=True)
        (blip_dir / "docker.yaml").write_text(yaml.dump({"blip": {"name": "Docker"}}))
        (blip_dir / "podman.yaml").write_text(yaml.dump({"blip": {"name": "Podman"}}))

        radar = Ingester(radar_dir, options=options).ingest()
        assert len(radar.blips) == 2
        names = {b.name for b in radar.blips}
        assert names == {"Docker", "Podman"}

    def test_specs_yml_extension(self, tmp_path, options):
        (tmp_path / "specs.yml").write_text(yaml.dump(SPECS))
        radar = Ingester(tmp_path, options=options).ingest()
        assert len(radar.rings_raw) == 4

    def test_non_yaml_files_ignored(self, radar_dir, options):
        blip_dir = radar_dir / "tools" / "adopt"
        blip_dir.mkdir(parents=True)
        (blip_dir / "docker.yaml").write_text(yaml.dump({"blip": {"name": "Docker"}}))
        (blip_dir / "README.md").write_text("ignore me")

        radar = Ingester(radar_dir, options=options).ingest()
        assert len(radar.blips) == 1
