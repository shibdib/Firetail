from setuptools import find_packages, setup

setup(
    name='firetail',
    version='1.0.0a0',
    description='firetail - An EVE Online Discord Bot',
    url='https://github.com/shibdib/firetail',
    author='shibdib',
    author_email='',
    license='GNU General Public License v3.0',

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Developers',
        'Topic :: Games/Entertainment :: Role-Playing',
        'Topic :: Communications :: Chat',
        'Topic :: Utilities',
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',
        'Programming Language :: Python :: 3.5',
    ],

    keywords='eve online eveonline community discord bot',

    # find_packages(exclude=['contrib', 'docs', 'tests'])
    packages=find_packages(),

    install_requires=[
        'discord.py[voice]',
        'python-dateutil>=2.6',
        'asyncpg>=0.13',
        'pytz',
        'youtube_dl',
        'aiohttp>=2.0.0,<2.3.0',
        'feedparser'
    ],

    dependency_links=[
        'git+https://github.com/Rapptz/discord.py@rewrite#egg=discord.py-1'
    ],

    package_data={
        'firetail': ['data/*.json'],
    },

    entry_points={
        'console_scripts': [
            'firetail=firetail.launcher:main',
            'firetail-bot=firetail.__main__:main'
        ],
    },
)
