from setuptools import setup, find_packages

# Read the README for the long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="snapgpt",
    version="0.1.1",
    author="Daniel Price",
    author_email="",
    description="A tool to create readable snapshots of your codebase",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/halfprice06/snapgpt",
    packages=find_packages(),
    install_requires=[
        "pathlib",
        "termcolor>=2.3.0",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    entry_points={
        'console_scripts': [
            'snapgpt=snapgpt.cli:main',
        ],
    },
    python_requires=">=3.7",
)
