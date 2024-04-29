import sys

if len(sys.argv) > 1:
    command_args = " ".join(sys.argv[1:])
    # Process the command-line arguments
    print("Command Arguments:", command_args)