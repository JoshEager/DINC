"""Set every container's timezone to this machine's."""

from .. import timezone


def prepare(ctx):
    if ctx.env.get("TZ"):
        return
    name = timezone.detect()
    ctx.env.set("TZ", name)
    ctx.log(f"Set the stack's timezone to {name}, the same as this machine.")
    ctx.log("To use a different one, change TZ in .env and run `docker compose up -d`.")
