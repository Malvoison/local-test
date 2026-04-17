"""Legacy script entry point that forwards to ``toolcli.main``."""

from toolcli.main import main


if __name__ == "__main__":
    raise SystemExit(main())
