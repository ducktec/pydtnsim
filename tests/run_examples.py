"""Run python files in the examples directory and check if they fail.

Helpful to detect issues in the examples that arose due to changes in the
core implementation.
"""
import sys
import os
import glob
import subprocess
from termcolor import colored


def main():
    """Run all files in example folder and check their return values."""
    return_value = 0

    # Switch to the examples directory
    os.chdir("examples")

    # For all python files found in the examples directory, execute the script
    # and check if it fails (based on the exit code)
    for file in glob.glob("*.py"):
        try:
            output = subprocess.check_output(['python3', file])
            print(output.decode("utf-8"))
            print(
                colored(
                    "----------\nExecution {} SUCCEEDED!\n----------".format(
                        file), 'green'))
        except subprocess.CalledProcessError as process_error:
            print(process_error.output.decode("utf-8"))
            print(
                colored(
                    "----------\nExecution of {} FAILED!\n----------".format(
                        file), 'red'))
            return_value = 1

    # Return the overall success (only 0 if all example files succeeded,
    # 1 otherwise)
    sys.exit(return_value)


if __name__ == "__main__":
    main()
