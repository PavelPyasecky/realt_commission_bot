import sys

from app.i18n import compile_translations


def main():
    if len(sys.argv) > 1 and sys.argv[1] not in ("compilemessages",):
        raise SystemExit("Unknown command")
    compile_translations()


if __name__ == "__main__":
    main()
