"""Isolated PDF inspection with Linux container resource limits."""

import json
import logging
import resource
import sys
from processor.app import InvalidPDF, inspect_pdf


def main():
    resource.setrlimit(resource.RLIMIT_CPU, (8, 8))
    ceiling = 768 * 1024 * 1024
    resource.setrlimit(resource.RLIMIT_AS, (ceiling, ceiling))
    logging.disable(logging.CRITICAL)
    try:
        print(json.dumps(inspect_pdf(sys.stdin.buffer.read())))
    except InvalidPDF as error:
        print(json.dumps({"error": str(error)}))


if __name__ == "__main__":
    main()
