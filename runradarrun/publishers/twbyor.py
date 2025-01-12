# -*- coding: utf-8 -*-
# code: language=python tabSize=4
#
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import docker

from ..model import AbstractPublisher
from ..output import Printer


class Publisher(AbstractPublisher):
    container_image = "wwwthoughtworks/build-your-own-radar:latest"
    container = None
    publishing_url = "http://localhost:8080/"
    run_output_file = "run-radar-run.json"

    @classmethod
    def cli_id(cls):
        return "twbyor"

    def make_output(self):
        results = []
        for blip in self.radar.blips:
            results.append(
                dict(
                    name=blip.name,
                    ring=blip.ring,
                    quadrant=blip.quadrant,
                    isNew="TRUE" if blip.is_new else "FALSE",
                    description=blip.description,
                )
            )

        return json.dumps(results)

    def run(self):
        with TemporaryDirectory(dir=".", prefix=".runradar-") as temp_dir:
            os.chmod(temp_dir, 0o755)
            temp_output = Path(temp_dir) / self.run_output_file
            self.write(temp_output)

            rd = self.radar
            client = docker.from_env()
            self.container = client.containers.run(
                self.container_image,
                auto_remove=True,
                ports={"80/tcp": 8080},
                environment={
                    "SERVER_NAMES": "localhost 127.0.0.1",
                    "QUADRANTS": json.dumps(
                        [q.name for q in rd.quadrants(rd.QUADRANTS_TL_BL_TR_BR)]
                    ),
                    "RINGS": json.dumps([r.name for r in rd.rings_outward()]),
                },
                volumes={
                    temp_dir: {"bind": "/opt/build-your-own-radar/files", "mode": "rw"}
                },
                detach=True,
                stream=True,
            )

            p = Printer(self.options.quiet)

            def trigger_browser(line):
                if "Starting nginx server..." in line:
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
        return (
            f"{self.publishing_url}"
            "?documentId=http%3A%2F%2Flocalhost%3A8080%2Ffiles%2F"
            f"{self.run_output_file}"
        )
