from setuptools import setup, find_packages

setup(
    name="snapgpt",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'snapgpt=snapgpt.cli:main',
        ],
    },
)
