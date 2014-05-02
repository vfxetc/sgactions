from setuptools import setup, find_packages

setup(
    name='sgactions',
    version='1.1.0',
    description='Shotgun ActionMenuItem enrichment.',
    url='http://github.com/westernx/sgactions',
    
    packages=find_packages(exclude=['build*', 'tests*']),
    
    author='Mike Boers',
    author_email='sgactions@mikeboers.com',
    license='BSD-3',
    
    install_requires='''
        pyyaml
    ''',

    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
