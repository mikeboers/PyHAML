
from distutils.core import setup

setup(
    name='PyHAML',
    version='0.1.3',
    description='Pythonic implementation of HAML, cross compiling to Mako template syntax.',
    url='http://github.com/mikeboers/PyHAML',
    author='Mike Boers',
    author_email='PyHAML@mikeboers.com',
    license='New BSD License',
    packages=['haml'],
    install_requires=['mako'],
    scripts=[
        'scripts/haml-preprocess',
        'scripts/haml-render',
    ],
)
