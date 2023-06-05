import sys

try:
    import final
except ModuleNotFoundError:
    print(
        f"final not found\nUse this command to install it {sys.executable} -m"
        + " pip install git+https://github.com/GrenManSK/final.git"
    )
    input()
    sys.exit(1)
try:
    import curses_builder
except ModuleNotFoundError:
    print(
        f"curse_builder not found\nUse this command to install it {sys.executable} -m"
        + " pip install git+https://github.com/GrenManSK/curses-builder.git"
    )
    input()
    sys.exit(1)
