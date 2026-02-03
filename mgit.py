import sys
from commands import *

def __main__():
    if len(sys.argv) < 2:
        print("Invalid usage. Please provide at least one argument.")
        sys.exit(1)
    else:
        match(sys.argv[1]):
            case "init":
                init()
            case "add":
                if len(sys.argv) < 3:
                    print("Please specify files to add.")
                else:
                    add(sys.argv[2:])
            case "commit":
                if len(sys.argv) < 3:
                    print("Please write a commit message.")
                else:
                    commit(sys.argv[2])
            case "status":
                status()
            case "log":
                log()
            case "checkout":
                if len(sys.argv) < 3:
                    print("Please specify a branch or commit to checkout.")
                else:
                    checkout(sys.argv[2])
            case _:
                print(f"Unknown command: {sys.argv[1]}")
if __name__ == "__main__":
    __main__()