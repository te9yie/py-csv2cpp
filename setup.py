from setuptools import setup

setup(
    name="csv2cpp",
    entry_point={
        "console_scripts": [
            "csv2cpp=csv2cpp.__main__:main",
        ],
    },
)
