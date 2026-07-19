from setuptools import find_packages, setup

setup(
    name="vayu-drishti",
    version="0.1.0",
    packages=find_packages(exclude=["tests", "tests.*"]),
    python_requires=">=3.12",
)
