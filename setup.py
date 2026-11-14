from setuptools import setup, find_packages
from typing import List

HYPHEN_E_DOT = "-e ."

def get_requirements(file_path: str) -> List[str]:
    requirements = []
    with open(file_path) as file_obj:
        for line in file_obj:
            line = line.strip()
            if line and not line.startswith("#") and line != HYPHEN_E_DOT:
                requirements.append(line)
    return requirements

setup(
    name="us_visa",
    version="0.0.0",
    author="Rishabh",
    author_email="rs6739171@gmail.com",
    packages=find_packages(),
    install_requires=get_requirements("requirements.txt")
)
