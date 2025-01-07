# -*- coding: utf-8 -*-
# code: language=python tabSize=4
#
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory

import docker
from blessed import Terminal

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

            try:
                log_height = 10
                term = Terminal()

                print(term.hide_cursor(), end="")
                print("\n" * (log_height + 1), end="")
                print(f"{term.move_up(log_height)}", end="")
                start_row, _ = term.get_location()

                log_lines = []
                for line in self.container.logs(stream=True):
                    log_lines.append(line.decode("utf-8").strip())
                    log_lines = log_lines[-log_height:]

                    with term.location(0, start_row):
                        for log_line in log_lines:
                            print(
                                f"{term.truncate(log_line)}{term.clear_eol()}",
                                flush=True,
                            )

                    line = line.decode("utf-8").strip()
                    if "Starting nginx server..." in line:
                        if not self.options.run_only:
                            self.open_url()
            finally:
                print(f"{term.normal_cursor()}{term.move_up()}{term.clear_eos()}")

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
