# -*- coding: utf-8 -*-
# code: language=python tabSize=4
#
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import docker
from git import Repo

from ..model import AbstractPublisher
from ..output import Printer


html_content = """\
<!DOCTYPE html>
<html lang="en">

<head>
<meta http-equiv="Content-type" content="text/html; charset=utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1" />
<title>Zalando Tech Radar</title>
<link rel="shortcut icon" href="https://www.zalando.de/favicon.ico">

<script src="https://d3js.org/d3.v4.min.js"></script>
<script src="radar.js"></script>

<link rel="stylesheet" href="radar.css">
</head>

<body>

<svg id="radar"></svg>

<script>
fetch('./config.json').then(function(response) {
  return response.json();
}).then(function(data) {
  radar_visualization(data);
}).catch(function(err) {
  console.log('Error loading config.json', err);
});
</script>

</body>
</html>
"""


class Publisher(AbstractPublisher):
    zalando_git_url = "https://github.com/zalando/tech-radar.git"
    container_image = "gcriocloudbuilders/yarn"
    container = None
    publishing_url = "http://localhost:8080/"
    ring_colors = ["#5ba300", "#009eb0", "#c7ba00", "#e09b96"]

    @property
    def quadrant_order(self):
        rd = self.radar
        return (rd.Q_BR, rd.Q_BL, rd.Q_TL, rd.Q_TR)

    @classmethod
    def cli_id(cls):
        return "zalando"

    def make_output(self):
        q_names = [q.name for q in self.radar.quadrants(self.quadrant_order)]
        r_names = [r.name for r in self.radar.rings_outward()]

        entries = [
            dict(
                quadrant=q_names.index(blip.quadrant),
                ring=r_names.index(blip.ring),
                label=blip.name,
                active=True,
                moved=(blip.ring != blip.previous_ring),
            )
            for blip in self.radar.blips
        ]

        output = dict(
            repo_url="https://github.com/zalando/tech-radar",
            title="Zalando Tech Radar",
            date="2025.01",  # kind of a version
            quadrants=[
                {"name": q.name} for q in self.radar.quadrants(self.quadrant_order)
            ],
            rings=[
                dict(
                    name=r.name.upper(),
                    color=c,
                )
                for r, c in zip(self.radar.rings_outward(), self.ring_colors)
            ],
            entries=entries,
        )
        return json.dumps(output)

    def run(self):
        with TemporaryDirectory(dir=".", prefix=".runradarrun-") as temp_dir:
            os.chmod(temp_dir, 0o755)

            repo_dir = Path(temp_dir) / "zalando"
            Repo.clone_from(self.zalando_git_url, repo_dir, depth=1)

            temp_output = repo_dir / "docs" / "config.json"
            self.write(temp_output)

            with open(repo_dir / "docs" / "index.html", "w") as index:
                index.write(html_content)

            p = Printer(self.options.quiet)

            client = docker.from_env()
            # Run bare yarn to install packages
            self.container = client.containers.run(
                self.container_image,
                auto_remove=True,
                volumes={repo_dir.as_posix(): {"bind": "/app", "mode": "rw"}},
                working_dir="/app",
                detach=True,
                stream=True,
                user=os.getuid(),
            )

            p.logger(
                stream=self.container.logs(stream=True),
                log_height=10,
            )

            # Run radar
            self.container = client.containers.run(
                self.container_image,
                auto_remove=True,
                ports={"3000/tcp": 8080},
                volumes={repo_dir.as_posix(): {"bind": "/app", "mode": "rw"}},
                working_dir="/app",
                detach=True,
                stream=True,
                command=["start", "--no-open"],
                user=os.getuid(),
            )

            def trigger_browser(line):
                if "Watching files..." in line:
                    self.open_url()

            p.logger(
                stream=self.container.logs(stream=True),
                log_height=10,
                trigger=trigger_browser,
            )

    def cleanup(self):
        if self.container:
            self.container.stop()

    @property
    def url(self):
        return self.publishing_url
