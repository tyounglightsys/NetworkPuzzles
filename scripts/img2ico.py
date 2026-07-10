#!/usr/bin/env python3

import argparse
import logging
import shutil
import subprocess
import sys
from pathlib import Path


def main():
    # Parse args.
    parser = argparse.ArgumentParser(
        prog=Path(__file__).name, description="convert image to an ICO file"
    )
    parser.add_argument("--debug", action="store_true")
    parser.add_argument('-v', "--verbose", action="store_true")
    parser.add_argument("IMAGE", nargs=1)
    args = parser.parse_args()

    # Set up logging.
    if args.debug:
        level = logging.DEBUG
    elif args.verbose:
        level = logging.INFO
    else:
        level = logging.WARNING
    logging.basicConfig(format="{levelname}: {message}", style="{", level=level)

    # Check for "convert" command in PATH.
    binary = "convert"
    if shutil.which(binary) is None:
        logging.error(f"System command not found: {binary}")
        sys.exit(1)

    # Get infile.
    infile_path = Path(args.IMAGE[0])
    if not infile_path.is_file():
        logging.error(f"File not found: {sys.argv[1]}")
        sys.exit(1)

    # Set outfile.
    outfile_path = infile_path.with_suffix(".ico")
    logging.debug(f"{outfile_path=}")

    # Run conversion.
    cmd = [
        "convert",
        str(infile_path),
        "-define",
        "icon:auto-resize=256,64,48,32,16",
        str(outfile_path),
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print(proc.stderr)


if __name__ == "__main__":
    main()
