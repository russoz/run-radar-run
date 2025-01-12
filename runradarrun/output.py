# -*- coding: utf-8 -*-
# code: language=python tabSize=4
#
from blessed import Terminal


class Printer:
    def __init__(self, quiet) -> None:
        self.quiet = quiet
        self._term = None

    @property
    def term(self) -> Terminal:
        if not self._term:
            self._term = Terminal()
        return self._term

    def print(self, *args, **kwargs) -> None:
        if not self.quiet:
            print(*args, **kwargs)

    def align_item(self, item: str) -> str:
        return self.term.rjust(item, 12)

    def logger(self, stream, log_height, trigger=None):
        try:
            self.print(
                self.term.hide_cursor
                + "\n" * (log_height + 1)
                + self.term.move_up(log_height),
                end="",
            )
            start_row, _ = self.term.get_location()

            log_lines = []
            for line in stream:
                line = line.decode("utf-8").strip()
                for line1 in self.term.wrap(line) or [""]:
                    log_lines.append((line1, len(line1) < self.term.width))

                log_lines = log_lines[-log_height:]
                with self.term.location(0, start_row):
                    for log_line, ending in log_lines:
                        self.print(
                            (
                                f"{self.term.red}{log_line}{self.term.normal + self.term.clear_eol}"
                                + "\n"
                                if ending
                                else ""
                            ),
                            end="",
                            flush=True,
                        )

                if trigger:
                    trigger(line)
        finally:
            print(f"{self.term.normal_cursor}{self.term.move_up}{self.term.clear_eos}")
