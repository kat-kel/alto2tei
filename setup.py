from setuptools import find_packages, setup

setup(
    name='alto2tei',
    version='0.0.1',
    packages=find_packages(),
    install_requires=[
        'certifi==2022.6.15',
        'charset-normalizer==2.1.0',
        'idna==3.3',
        'lxml==4.9.1',
        'PyYAML==6.0',
        'requests==2.28.1',
        'urllib3==1.26.11'
    ],
    entry_points={
        'console_scripts': [
            'alto2tei=src.__main__:main'
        ]
    }

)