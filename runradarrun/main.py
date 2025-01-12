#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# code: language=python tabSize=4
#
import argparse
import pathlib

from runradarrun.ingest import Ingester
from runradarrun.output import Printer
from runradarrun.publishers.twbyor import TXBYORPublisher


publishers = {
    "twbyor": TXBYORPublisher,
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        "-i",
        type=pathlib.Path,
        default="./radar",
        help="radar input file in YAML format",
    )
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

    args = parser.parse_args()
    ingester = Ingester(pathlib.Path(args.input), options=args)
    radar = ingester.ingest()

    if args.publisher:
        p = Printer(args.quiet)

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
            except KeyboardInterrupt:
                pass
            finally:
                publisher.cleanup()


if __name__ == "__main__":
    main()
