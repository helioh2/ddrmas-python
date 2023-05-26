import argparse
import logging
import sys

from ddrmas_python import __version__
from ddrmas_python.services.load_system_from_file import load_system_from_file
from ddrmas_python.services.print_system import print_system

__author__ = "Helio"
__copyright__ = "Helio"
__license__ = "MIT"

_logger = logging.getLogger(__name__)

def parse_args(args):
    """Parse command line parameters

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--help"]``).

    Returns:
      :obj:`argparse.Namespace`: command line parameters namespace
    """
    parser = argparse.ArgumentParser(description="Just a Fibonacci demonstration")
    parser.add_argument(
        "--version",
        action="version",
        version=f"ddrmas-python {__version__}",
    )
    parser.add_argument(dest="filename", help="Filename", type=str, metavar="STR")
    parser.add_argument(
        "-v",
        "--verbose",
        dest="loglevel",
        help="set loglevel to INFO",
        action="store_const",
        const=logging.INFO,
    )
    parser.add_argument(
        "-vv",
        "--very-verbose",
        dest="loglevel",
        help="set loglevel to DEBUG",
        action="store_const",
        const=logging.DEBUG,
    )
    return parser.parse_args(args)


def setup_logging(loglevel):
    """Setup basic logging

    Args:
      loglevel (int): minimum loglevel for emitting messages
    """
    logformat = "[%(asctime)s] %(levelname)s:%(name)s:%(message)s"
    logging.basicConfig(
        level=loglevel, stream=sys.stdout, format=logformat, datefmt="%Y-%m-%d %H:%M:%S"
    )


def main(args):
    """Wrapper allowing :func:`load_system_from_file` to be called with 
    string arguments in a CLI fashion

    Instead of returning the value from :func:`load_system_from_file`, it prints the result to the
    ``stdout`` in a nicely formatted message.

    Args:
      args (List[str]): command line parameters as list of strings
          (for example  ``["--verbose", "42"]``).
    """
    args = parse_args(args)
    setup_logging(args.loglevel)
    _logger.debug("Loading DDRMAS system.")
    
    system = load_system_from_file(args.filename)

    print_system(system)

    while True:

        emitter_agent_name = input("Enter the identifier of the agent that will send the initial query: ")

        literal = input("Enter the literal to query: ")

        while True:

            focus_rule = input("Enter a focus rule to send with the query, or type 'done' to finish: ")
            if focus_rule == "done":
                break

            

    _logger.debug("Starting interactive code.")

    _logger.info("Script ends here")


def run():
    """Calls :func:`main` passing the CLI arguments extracted from :obj:`sys.argv`

    This function can be used as entry point to create console scripts with setuptools.
    """
    main(sys.argv[1:])


if __name__ == "__main__":
    # ^  This is a guard statement that will prevent the following code from
    #    being executed in the case someone imports this file instead of
    #    executing it as a script.
    #    https://docs.python.org/3/library/__main__.html

    # After installing your project with pip, users can also run your Python
    # modules as scripts via the ``-m`` flag, as defined in PEP 338::
    #
    #     python -m ddrmas_python.skeleton 42
    #
    run()