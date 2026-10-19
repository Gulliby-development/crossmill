from crossmill.base.fail import Fail
from crossmill.base.inputs import IO
from crossmill.base.options import parse_options
from crossmill.base.text import show
from crossmill.cli import (
    cmd_check,
    cmd_count,
    cmd_domains,
    cmd_fill,
    cmd_forced,
    cmd_number,
    cmd_pattern,
    cmd_render,
    cmd_stats,
    cmd_symmetrize,
)

_COMMANDS = {
    "check": cmd_check,
    "number": cmd_number,
    "render": cmd_render,
    "symmetrize": cmd_symmetrize,
    "pattern": cmd_pattern,
    "stats": cmd_stats,
    "domains": cmd_domains,
    "forced": cmd_forced,
    "fill": cmd_fill,
    "count": cmd_count,
}


def run(args: list[str], io: IO) -> int:
    """Dispatch one command, writing its complete report or one user-facing error."""
    try:
        if not args:
            raise Fail(
                "missing command (check, number, render, symmetrize, pattern, stats, "
                "domains, forced, fill or count)"
            )

        command = args[0]
        module = _COMMANDS.get(command)
        if module is None:
            raise Fail(f"unknown command {show(command)}")

        options, ordinary = parse_options(args[1:], module.SPECS)
        if len(ordinary) != module.ARGS:
            raise Fail(f"usage: {module.USAGE}")

        report, status = getattr(module, f"run_{command}")(ordinary, options, io)
    except Fail as error:
        io.err(f"crossmill: {error}\n")
        return 2

    io.out(report)
    return status
