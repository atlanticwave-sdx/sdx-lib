from setuptools import setup, find_packages

setup(
    name="sdxlib",
    version="0.1",
    packages=find_packages(),
    install_requires=["requests", "pycountry", "dacite",],
)
