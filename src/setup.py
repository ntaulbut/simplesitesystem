from setuptools import setup, find_packages

setup(
    name="simple",
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "click", "tomli", "jinja2", "pyquery", "pygments"
    ],
    entry_points={
        "console_scripts": [
            "simple = simplesitesystem.main:simplesitesystem",
        ],
    },
)
