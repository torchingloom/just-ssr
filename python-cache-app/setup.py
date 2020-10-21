from setuptools import setup, find_packages

setup(
    name='just-cache-app',
    version='0.0.1a0',
    entry_points={
        'console_scripts': [
            'python-cache-app=cache_app.cli:cli',
        ],
    },
    packages=find_packages('src'),
    package_dir={'': 'src'},
)
