from setuptools import setup, find_packages
import pathlib


LIB_NAME = 'mangagraph'
WORK_DIR = pathlib.Path(__file__).parent
VERSION = '0.1.0'

try:
    long_description = (WORK_DIR / "readme.md").read_text("utf-8")
except FileNotFoundError:
    long_description = "Async manga parser-converter from mangalib to telegraph pages"

setup(
    name=LIB_NAME,
    version=VERSION,
    description='Async manga parser-converter from mangalib to telegraph pages',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/damirTAG/mangagraph',
    author='damirTAG',
    author_email='damirtagilbayev17@gmail.com',
    license='MIT',
    packages=find_packages(exclude=['tests', 'tests.*']),
    install_requires=[
        'aiohttp>=3.8.0',
        'sqlalchemy>=1.4.0',
        'telegraph>=2.2.0'
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-asyncio>=0.21.0',
            'black>=23.0.0',
            'flake8>=6.0.0',
        ]
    },
    classifiers=[
        # Development Status
        'Development Status :: 3 - Alpha',
        
        # Intended Audience
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Internet :: WWW/HTTP',
        
        # License
        'License :: OSI Approved :: MIT License',
        
        # Python versions - based on async/await and type hints usage
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3 :: Only',
        
        # OS
        'Operating System :: OS Independent',
        
        # Framework
        'Framework :: AsyncIO',
        
        # Typing
        'Typing :: Typed',
    ],
    keywords=[
        'mangalib',
        'mangalib-parser',
        'manga',
        'telegraph',
        'async',
        'parser',
        'converter',
        'web-scraping',
    ],
    python_requires='>=3.8',
    include_package_data=True, 
    project_urls={
        'Bug Reports': 'https://github.com/damirTAG/mangagraph/issues',
        'Source': 'https://github.com/damirTAG/mangagraph',
        'Telegram': 'https://t.me/damirtag',
    },
    zip_safe=False,
)