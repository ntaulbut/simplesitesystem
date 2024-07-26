import click

from commands import build, dev


@click.group()
def simplesitesystem():
    pass


# noinspection PyTypeChecker
simplesitesystem.add_command(build)
# noinspection PyTypeChecker
simplesitesystem.add_command(dev)

# A rendered template is a page
# Non-template files in the source directory are assets

if __name__ == "__main__":
    simplesitesystem()
