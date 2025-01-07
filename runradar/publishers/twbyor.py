# -*- coding: utf-8 -*-
# code: language=python tabSize=4
#
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import docker

from ..model import Publisher


class TXBYORPublisher(Publisher):
    container_image = "wwwthoughtworks/build-your-own-radar:latest"
    container = None
    publishing_url = "http://localhost:8080/"
    run_output_file = "runradar.json"

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
        with TemporaryDirectory(dir=".") as temp_dir:
            os.chmod(temp_dir, 0o755)
            temp_output = Path(temp_dir) / self.run_output_file
            self.write(temp_output)

            client = docker.from_env()
            self.container = client.containers.run(
                self.container_image,
                auto_remove=True,
                ports={"80/tcp": 8080},
                environment={
                    "SERVER_NAMES": "localhost 127.0.0.1",
                    "QUADRANTS": json.dumps(list(q.name for q in self.radar.quadrants)),
                    "RINGS": json.dumps(list(r.name for r in self.radar.rings)),
                },
                volumes={
                    temp_dir: {"bind": "/opt/build-your-own-radar/files", "mode": "rw"}
                },
                detach=True,
                stream=True,
            )
            for line in self.container.logs(stream=True):
                print(line.decode("utf-8").strip())

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
