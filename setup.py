from setuptools import setup, find_packages
from os import path

here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name="aiCamera",
    version="1.0.0",
    description="aiCamera component for Devposts Facebook AI hackathon",
    long_description_content_type="text/markdown",
    url="TODO",
    author="Stephen Mott, Rico Beti",
    classifiers=["Development Status ::3 - Alpha",
                 "Intended Audience :: Developers",
                 "Topic :: Software Development :: Machine Learning",
                 "Programming Language :: Python :: 3.7"],
    packages=find_packages(where='src'),
    python_requires=">=3.5",
    platforms="Raspbian",
    entry_points={'console_scripts': [
        'cameraai = aicam.cli:cli'
    ]}
)
