from setuptools import setup, find_packages

setup(
    name='txt2kb',
    version='0.1.0',
    packages=find_packages(),
    install_requires=[
        transformers
        git+http://github.com/mrdavtan/wikipedia.git@beautifulsoup_warning_fix#egg=wikipedia
        newspaper3k
        GoogleNews
        pyvis
        torch
        torchvision
        lxml
    ],
    # Include additional metadata about your package
)
