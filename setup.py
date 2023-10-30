from setuptools import setup

setup(
    name="csv2cpp",
    entry_points={
        "console_scripts": [
            "csv2cpp = csv2cpp.__main__:main",
        ],
    },
)
