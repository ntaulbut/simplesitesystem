import click
from aiohttp import web
from os.path import join

from simplesitesystem.build import build_internal
from simplesitesystem.dev_server import create_websocket_handler


# noinspection DuplicatedCode
@click.command()
@click.argument(
    "source_dir", type=click.Path(file_okay=False, dir_okay=True, exists=True)
)
@click.argument(
    "output_dir", type=click.Path(file_okay=False, dir_okay=True, writable=True)
)
@click.option(
    "-s",
    "--strings",
    "strings_file",
    type=click.Path(file_okay=True, dir_okay=False, exists=True),
    help="Translations file.",
)
@click.option(
    "-d",
    "--data",
    "data_file",
    type=click.Path(file_okay=True, dir_okay=False, exists=True),
    help="JSON data to supply to templates.",
)
@click.option("--no-symlink-assets", default=False, is_flag=True)
def build(
    source_dir: str,
    output_dir: str,
    strings_file: str,
    data_file: str,
    no_symlink_assets: bool,
) -> None:
    build_internal(
        source_dir, output_dir, strings_file, data_file, no_symlink_assets, False
    )


# noinspection DuplicatedCode
@click.command()
@click.argument(
    "source_dir", type=click.Path(file_okay=False, dir_okay=True, exists=True)
)
@click.argument(
    "output_dir", type=click.Path(file_okay=False, dir_okay=True, writable=True)
)
@click.option(
    "-s",
    "--strings",
    "strings_file",
    type=click.Path(file_okay=True, dir_okay=False, exists=True),
    help="Translations file.",
)
@click.option(
    "-d",
    "--data",
    "data_file",
    type=click.Path(file_okay=True, dir_okay=False, exists=True),
    help="JSON data to supply to templates.",
)
@click.option("--no-symlink-assets", default=False, is_flag=True)
def dev(
    source_dir: str,
    output_dir: str,
    strings_file: str,
    data_file: str,
    no_symlink_assets: bool,
) -> None:
    build_internal(
        source_dir, output_dir, strings_file, data_file, no_symlink_assets, True
    )
    app = web.Application()
    websocket_handler = create_websocket_handler(
        source_dir, output_dir, strings_file, data_file, no_symlink_assets
    )
    app.add_routes(
        [
            web.get("/websocket_", websocket_handler),
            web.static("/", join(output_dir, "dev"), show_index=True),
        ]
    )
    web.run_app(app)
