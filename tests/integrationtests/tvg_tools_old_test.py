"""Verify that pydtnsim works with the old tvg_tools."""

import sys
from termcolor import colored
from pydtnsim.contact_plan import ContactPlan


def main():
    """Check legacy tvg json file compatibility"""
    # Generate contact plan from provided json file
    # The file represents the typical output of the old tvg_tools
    try:
        contact_plan = ContactPlan(1000, 10,
                                   "tests/resources/tvg_g10_s10.json")
    except Exception as e:
        print(
            colored(
                "Generating contact plan based on legacy tvg json file "
                "failed!", 'red'))
        sys.exit(1)

    print(
        colored(
            "Generating contact plan based on legacy tvg json file "
            "succeeded!", 'green'))


if __name__ == "__main__":
    main()
