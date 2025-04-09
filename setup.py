from setuptools import setup, find_packages

import pathlib


LIB_NAME = 'mangagraph'

WORK_DIR = pathlib.Path(__file__).parent

VERSION = '0.0.3.post6'

setup(
    name=LIB_NAME,
    version=VERSION,
    description='Async manga parser-converter from mangalib to telegraph pages',
    long_description = (WORK_DIR / "readme.md").read_text("utf-8"),
    long_description_content_type='text/markdown',
    url='https://github.com/damirTAG/mangagraph',
    author='damirTAG',
    author_email='damirtagilbayev17@gmail.com',
    packages=find_packages(),
    install_requires=[
        'aiohttp',
        'sqlalchemy',
        'telegraph',
        'asyncio'
    ],
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    keywords=[
        'mangalib',
        'mangalib-parser',
        'manga',
        'telegraph'
    ],
    python_requires='>=3.7',
    include_package_data=False
)