from setuptools import setup, find_packages

setup(
    name = 'mcparthenon',
    author = 'Rich Wareham',
    author_email = 'rich.mcparthenon@richwareham.com',
    description = 'Quick hack to convert the Parthenon scultpures to a Minecraft map',
    license = 'MIT',
    packages=find_packages(exclude=['tests']),
    setup_requires=[
        # Because pymclevel does not list *all* of its dependencies
        'cython',
        'numpy',
        'pyyaml',
    ],
    install_requires=[
        'docopt',
        'pillow',
        'pymclevel',
    ],
    dependency_links = [
        'https://github.com/mcedit/pymclevel/tarball/master#egg=pymclevel'
    ],
    entry_points = {
        'console_scripts': [
            'makelevel = mcparthenon.makelevel:main',
        ],
    },
    package_data={
        'mcparthenon': ['data/*.yaml']
    },
)
