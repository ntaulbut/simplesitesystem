import os


def extension(filename: str) -> str:
    """
    :param filename: index.html.jinja
    :return: .jinja
    """
    return os.path.splitext(filename)[1]


def strip_exts(filename: str) -> str:
    """
    :param filename: index.html.jinja
    :return: index
    """
    return filename.split(os.extsep)[0]
