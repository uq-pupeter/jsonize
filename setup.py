__author__ = 'EUROCONTROL (SWIM)'

import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="jsonize",
    version="0.0.1",
    author="EUROCONTROL (SWIM)",
    author_email="francisco-javier.crabiffosse.ext@eurocontrol.int",
    description="A simple library to convert XML documents into JSON",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/eurocontrol-swim/jsonize",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'jsonschema>=3.2.0',
        'pyparsing>=2.4.6',
        'lxml>=4.5.0'
    ]
)
