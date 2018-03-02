from setuptools import find_packages
from setuptools import setup

import versioneer

setup(
    author='',
    cmdclass=versioneer.get_cmdclass(),
    description='',
    license='',
    long_description='',
    maintainer='',
    name='scrapy-proxy-management',
    packages=find_packages(
        exclude=('tests', 'tests.*')
    ),
    install_requires=[
        'scrapy',
        'twisted',
    ],
    version=versioneer.get_version(),
)
