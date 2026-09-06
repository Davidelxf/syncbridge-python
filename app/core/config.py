from os import getenv


def get_cursor_signing_key() -> str:
    signing_key = getenv("CURSOR_SIGNING_KEY")

    if not signing_key:
        raise RuntimeError("CURSOR_SIGNING_KEY environment variable is required")

    return signing_key
