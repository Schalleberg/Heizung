"""This Python script starts the Pydev debugger in eclipse and displays output
on the eclipse console"""

import sys
import os
import datetime

import pydevd


HOST = "NOTEBOOK"
"""Can be an IP address or hostname"""


def remote_debug_setup():
    """Function for Pydev Python debug"""
    try:

        # If you want to break as soon as the pydevd.sttrace
        # function below is called set "suspend=True and the debug will start
        # on the next line of python code after pydevd.settrace().
        # if you want set a break point some else in your code change "suspend=False" and
        # insert "pydevd.settrace()" function where you want the break point.
        # pydevd.settrace('Remote IP address or hostname',port=5678, suspend=True)
        # stdoutToServer and stderrToServer redirects stdout and stderr to eclipse console

        pydevd.settrace(
            HOST, port=5678, stdoutToServer=True, stderrToServer=True, suspend=False
        )

        now = datetime.datetime.now()
        print(now.strftime("%d/%m/%Y %H:%M:%S ") + "Remote Debug works")
        # Here we set a break point
        pydevd.settrace()

    except NameError:
        sys.stderr.write(
            "\nError: "
            + 'Can not "import pydevd"\n\n'
            + "Use this command to install\n"
            + '"pip3 install pydev"\n\n'
        )
        sys.exit(1)


def main():
    """Main"""

    remote_debug_setup()

    print("Goodbye")


if __name__ == "__main__":
    main()