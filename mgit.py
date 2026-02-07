#!/usr/bin/env python3
import sys
from commands import *

def main():
    if len(sys.argv) < 2:
        print("Invalid usage. Please provide at least one argument.")
        return
    else:
        match(sys.argv[1]):
            case "init":
                if len(sys.argv) > 3:
                    print("Too many arguments")
                    sys.exit(1)
                init()
            case "add":
                if len(sys.argv) < 3:
                    print("Please specify files to add.")
                    sys.exit(1)
                else:
                    if sys.argv[2] == ".":
                        add_all()
                    add(sys.argv[2:])
            case "commit":
                if len(sys.argv) < 3:
                    print("Please write a commit message.")
                    sys.exit(1)
                else:
                    commit(sys.argv[2])
            case "status":
                if len(sys.argv) > 3:
                    print("Too many arguments")
                    sys.exit(1)
                status()
            case "log":
                if len(sys.argv) > 3:
                    print("Too many arguments")
                    sys.exit(1)
                log()
            case "checkout":
                if len(sys.argv) < 3:
                    print("Please specify a branch or commit to checkout.")
                    sys.exit(1)
                else:
                    checkout(sys.argv[2])
            case "unstage":
                if len(sys.argv) > 3:
                    print("Too many arguments")
                    sys.exit(1)
                unstage()
            case "-rh":
                if len(sys.argv) > 3:
                    print("Too many arguments")
                    sys.exit(1)
                restore_head()
            case _:
                print(f"Unknown command: {sys.argv[1]}")
if __name__ == "__main__":
    main()