#!/usr/bin/env python3
"""
Simple script to read a text file and print its contents to stdout.
"""

import sys


def read_and_print(filename):
    """Read a file and print its contents to stdout."""
    try:
        with open(filename, 'r') as f:
            contents = f.read()
            print(contents)
    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.", file=sys.stderr)
        sys.exit(1)
    except IOError as e:
        print(f"Error reading file: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <filename>", file=sys.stderr)
        sys.exit(1)

    read_and_print(sys.argv[1])
