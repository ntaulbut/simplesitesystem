import json
import os
import shutil
from typing import Callable

import tomli
from jinja2 import Environment, FileSystemLoader, Template

from simplesitesystem.extensions import CodeBlockExtension
from simplesitesystem.template_functions import get_autolink, code_style
from simplesitesystem.tools import extension, strip_exts

type Localizations = dict[str, dict[str, str]]

IGNORE = ".simpleignore"
DEV_SCRIPT = """<script>
const socket = new WebSocket("ws://localhost:8080/websocket_");
socket.onopen = () => {
    socket.send(location.pathname);
};
socket.onmessage = (event) => {
    const [instruction, argument] = event.data.split(" ");

    if (instruction === "reload") {
        location.reload();
    } else if (instruction === "go_to") {
        location.replace(argument);
    }
};
</script>
"""


def build_internal(
    source_dir: str,
    output_dir: str,
    strings_file: str,
    data_file: str,
    no_symlink_assets: bool = False,
    dev_mode: bool = False,
) -> None:
    jinja_env: Environment = Environment(
        loader=FileSystemLoader(source_dir),
        extensions=[CodeBlockExtension],
        trim_blocks=True,
        lstrip_blocks=True,
    )

    output_dir = os.path.join(output_dir, "dev/" if dev_mode else "release/")

    # Look for file containing newline-separated template names to exclude
    ignore: list[str] = []
    try:
        with open(IGNORE, "r") as f:
            ignore = [p.strip() for p in f.readlines()]
            print("Excluding:", ", ".join(ignore))
    except FileNotFoundError:
        print(f"{IGNORE} not found.")

    # Delete contents of output directory, if it exists
    shutil.rmtree(os.path.join(output_dir, "."), ignore_errors=True)

    # Load in all templates that are not ignored
    print("Loading templates...")
    templates: list[Template] = [
        jinja_env.get_template(path)
        for path in jinja_env.list_templates(extensions="jinja")
        if path not in ignore
    ]

    # Load the data file if it exists
    data = None
    if data_file:
        with open(data_file) as f:
            data = json.load(f)
        print(f"Loaded data file {data_file}")

    print("Rendering...")

    # If no localizations are provided
    if strings_file is None:
        render: Callable = get_renderer(templates, output_dir, data=data)
        shutil.copytree(
            source_dir,
            output_dir,
            ignore=shutil.ignore_patterns("*.jinja"),
            dirs_exist_ok=True,
        )
        for template in templates:
            render(template)
        return

    localizations: Localizations = read_localizations(strings_file)
    if len(localizations) == 0:
        print("No localizations in strings file.")
        return
    render: Callable = get_renderer(
        templates, output_dir, dev_mode, localizations=localizations
    )
    first_locale: str = next(iter(localizations))  # en
    first_locale_dir: str = os.path.join(output_dir, first_locale)  # output/en

    for locale in localizations:
        print(f"Rendering locale {locale}...")
        locale_dir: str = os.path.join(output_dir, locale)  # output/jp

        # For the first locale, copy all assets into its output directory.
        # For all subsequent locales, symlink to the assets in the first locale's output directory.
        if locale == first_locale or no_symlink_assets:
            shutil.copytree(
                source_dir,
                locale_dir,
                ignore=shutil.ignore_patterns("*.jinja"),
                dirs_exist_ok=True,
            )
        else:
            for filepath in assets(source_dir):
                symlink(
                    os.path.relpath(filepath, source_dir),
                    locale_dir,
                    first_locale_dir,
                )

        for template in templates:
            render(template, locale)


def get_renderer(
    templates: list[Template], output_dir: str, dev_mode: bool = False, **kwargs
) -> Callable:
    """
    :param dev_mode:
    :param templates: List of all Templates
    :param output_dir: output/
    :return: RenderLocale function
    """
    localizations = kwargs.get("localizations", {})
    data = kwargs.get("data", {})
    pages: list[str] = []

    def render(template: Template, locale: str = "") -> str:
        """
        :param locale: Locale to render template with, e.g. en
        :param template: Template to render
        :return: Path the template was written to
        """
        page_path: str = (
            strip_exts(os.path.join(output_dir, locale, template.name)) + ".html"
        )
        page_dir: str = os.path.dirname(page_path)
        os.makedirs(page_dir, exist_ok=True)
        if page_path not in pages:
            with open(page_path, "w") as f:
                f.write(
                    template.render(
                        autolink=get_autolink(
                            os.path.dirname(template.name),
                            page_path,
                            locale,
                            templates,
                            render,
                            dev_mode,
                        ),
                        strings=localizations[locale] if locale else None,
                        locale=locale,
                        data=data,
                        code_style=code_style,
                        dev_script=DEV_SCRIPT if dev_mode else "",
                    )
                )
            pages.append(page_path)

        return page_path

    return render


def symlink(asset_filepath: str, locale_dir: str, first_locale_dir: str) -> None:
    """
    Creates a relative symlink from `output/jp/img/catpicture.jpg` to `output/en/img/catpicture.jpg`.
    e.g. ../../en/img/catpicture.jpg.

    :param asset_filepath: img/catpicture.jpg
    :param locale_dir: output/jp/
    :param first_locale_dir: output/en/
    """
    # output/jp/img/catpicture.jpg
    new_filepath = os.path.join(locale_dir, asset_filepath)
    # output/en/img/catpicture.jpg
    existing_filepath = os.path.join(first_locale_dir, asset_filepath)
    # output/jp/img/
    new_file_dir = os.path.dirname(new_filepath)
    # output/en/img/
    existing_file_dir = os.path.dirname(existing_filepath)

    os.makedirs(new_file_dir, exist_ok=True)
    os.symlink(
        os.path.join(
            os.path.relpath(existing_file_dir, new_file_dir),
            os.path.basename(asset_filepath),
        ),
        new_filepath,
    )


def read_localizations(path: str) -> Localizations:
    try:
        with open(path, "rb") as f:
            try:
                return tomli.load(f)
            except tomli.TOMLDecodeError:
                exit(f"{path} is not a valid TOML file.")
    except FileNotFoundError:
        exit(f"{path} does not exist.")


def assets(source_dir: str) -> list[str]:
    for directory, subdirectories, filenames in os.walk(source_dir):
        for filename in filenames:
            if extension(filename) != ".jinja":
                yield os.path.join(directory, filename)
