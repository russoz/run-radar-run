import pytest

from runradarrun.model import Blip, Quadrant, Radar, RadarException, Ring


def make_rings():
    return {
        "inner": Ring(id="adopt", name="Adopt"),
        "mid_inner": Ring(id="trial", name="Trial"),
        "mid_outer": Ring(id="assess", name="Assess"),
        "outer": Ring(id="hold", name="Hold"),
    }


def make_quadrants():
    return {
        "top_left": Quadrant(id="strat", name="Strategies"),
        "top_right": Quadrant(id="tools", name="Tools"),
        "bottom_left": Quadrant(id="techniques", name="Techniques"),
        "bottom_right": Quadrant(id="lang", name="Languages"),
    }


class TestBlip:
    def test_is_new_when_no_previous_ring(self):
        blip = Blip(name="Docker", ring="Adopt", quadrant="Tools")
        assert blip.is_new is True

    def test_not_new_when_previous_ring_set(self):
        blip = Blip(name="Docker", ring="Adopt", quadrant="Tools", previous_ring="Trial")
        assert blip.is_new is False

    def test_str_new(self):
        blip = Blip(name="Docker", ring="Adopt", quadrant="Tools")
        assert "NEW" in str(blip)

    def test_str_not_new(self):
        blip = Blip(name="Docker", ring="Adopt", quadrant="Tools", previous_ring="Trial")
        assert "NEW" not in str(blip)

    def test_defaults_empty_lists(self):
        blip = Blip(name="X", ring="Adopt", quadrant="Tools")
        assert blip.description == []
        assert blip.references == []
        assert blip.tags == []


class TestRadar:
    def test_valid_radar(self):
        radar = Radar(make_rings(), make_quadrants())
        assert len(radar.rings_raw) == 4
        assert len(radar.quadrants_raw) == 4

    def test_three_rings_valid(self):
        rings = {k: v for k, v in list(make_rings().items())[:3]}
        radar = Radar(rings, make_quadrants())
        assert len(radar.rings_raw) == 3

    def test_too_few_rings_raises(self):
        rings = {k: v for k, v in list(make_rings().items())[:2]}
        with pytest.raises(RadarException):
            Radar(rings, make_quadrants())

    def test_too_many_rings_raises(self):
        rings = make_rings()
        rings["extra"] = Ring(id="extra", name="Extra")
        with pytest.raises(RadarException):
            Radar(rings, make_quadrants())

    def test_wrong_quadrant_count_raises(self):
        quadrants = {k: v for k, v in list(make_quadrants().items())[:3]}
        with pytest.raises(RadarException):
            Radar(make_rings(), quadrants)

    def test_add_blip(self):
        radar = Radar(make_rings(), make_quadrants())
        blip = Blip(name="Ansible", ring="Adopt", quadrant="Tools")
        radar.add_blip(blip)
        assert len(radar.blips) == 1
        assert radar.blips[0] is blip

    def test_rings_outward_order(self):
        radar = Radar(make_rings(), make_quadrants())
        names = [r.name for r in radar.rings_outward()]
        assert names == ["Adopt", "Trial", "Assess", "Hold"]

    def test_rings_inward_order(self):
        radar = Radar(make_rings(), make_quadrants())
        names = [r.name for r in radar.rings_inward()]
        assert names == ["Hold", "Assess", "Trial", "Adopt"]

    def test_quadrants_order(self):
        radar = Radar(make_rings(), make_quadrants())
        names = [q.name for q in radar.quadrants(Radar.QUADRANTS_CLOCKWISE)]
        assert names == ["Strategies", "Tools", "Languages", "Techniques"]
