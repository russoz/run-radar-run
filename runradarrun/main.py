#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# code: language=python tabSize=4
#
import argparse
import importlib
import pathlib
import pkgutil

import runradarrun.publishers
from runradarrun.ingest import Ingester
from runradarrun.model import RadarException
from runradarrun.output import Printer


def iter_namespace(ns_pkg):
    # Specifying the second argument (prefix) to iter_modules makes the
    # returned name an absolute name instead of a relative one. This allows
    # import_module to work without having to do additional modification to
    # the name.
    return pkgutil.iter_modules(ns_pkg.__path__, ns_pkg.__name__ + ".")


def load_publishers():
    return {
        publisher.cli_id(): publisher
        for finder, name, ispkg in iter_namespace(runradarrun.publishers)
        for publisher in [getattr(importlib.import_module(name), "Publisher")]
    }


def main():
    publishers = load_publishers()

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--publisher",
        "-P",
        default="twbyor",
        choices=sorted(publishers.keys()),
        help="publisher for the data radar",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=pathlib.Path,
        help="output path for the radar data, depends on publisher",
    )
    parser.add_argument(
        "--run",
        "-r",
        help="run the radar opens it in browser, depends on publisher",
        action="store_true",
    )
    parser.add_argument(
        "--run-only",
        "-R",
        help="only run the radar, depends on publisher",
        action="store_true",
    )
    parser.add_argument(
        "--quiet",
        "-q",
        help="do not print output",
        action="store_true",
    )
    parser.add_argument(
        "input",
        type=pathlib.Path,
        nargs="?",
        default="./radar",
        help="radar definition directory",
    )

    try:
        args = parser.parse_args()
        p = Printer(args.quiet)
        ingester = Ingester(pathlib.Path(args.input), options=args)
        radar = ingester.ingest()
        p.print(
            f"{p.align_item('Radar Path')}: {p.term.bold_yellow(str(ingester.radar_path.absolute()))}"
        )
        p.print(
            f"{p.align_item('Rings')}: {', '.join(p.term.bold_green(r.name) for r in radar.rings_raw.values())}"
        )
        p.print(
            f"{p.align_item('Quadrants')}: {', '.join(p.term.bold_green(q.name) for q in radar.quadrants_raw.values())}"
        )
        p.print(
            f"{p.align_item('Processed')}: {p.term.bold_green}{len(radar.blips):2} blips{p.term.normal + p.term.clear_eol}"
        )

        if args.publisher:
            publisher_class = publishers[args.publisher]
            publisher = publisher_class(radar, options=args)

            if args.output:
                publisher.write(args.output)

            if args.run or args.run_only:
                try:
                    p.print(
                        f"{p.align_item('Radar URL')}: {p.term.bold_blue}{p.term.link(publisher.url, publisher.url)}{p.term.normal}"
                    )
                    publisher.run()
                finally:
                    publisher.cleanup()
    except KeyboardInterrupt:
        pass
    except RadarException as e:
        print(f"\n{p.term.bold_red}ERROR: {e}{p.term.normal}")


if __name__ == "__main__":
    main()
