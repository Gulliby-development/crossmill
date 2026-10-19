import sys

from crossmill.base.inputs import StdIO
from crossmill.cli.cli import run

if __name__ == "__main__":
    sys.exit(run(sys.argv[1:], StdIO()))
