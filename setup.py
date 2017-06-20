import os

from setuptools import setup, find_packages


setup(
    name='sgactions',
    version='1.1.0',
    description='Shotgun ActionMenuItem enrichment.',
    url='http://github.com/westernx/sgactions',
    
    packages=find_packages(exclude=['build*', 'tests*']),
    include_package_data=True,

    author='Mike Boers',
    author_email='sgactions@mikeboers.com',
    license='BSD-3',

    install_requires='''
        pyyaml
    ''',

    entry_points={
        'console_scripts': '''
            sgactions-deploy = sgactions.deploy:main
            sgactions-install = sgactions.install:main
        ''',
    },

    metatools_apps=[{

        'name': 'SGActions',
        'identifier': 'com.westernx.sgactions',
        'target_type': 'entrypoint',
        'target': 'sgactions.dispatch:main',
        'use_compiled_bootstrap': True,
        'icon': 'sgactions/art/sgactions.icns',

        'url_schemes': ['sgaction'],
        'argv_emulation': True,
        
        # Bake in the development path if we are in dev mode.
        'python_path': os.environ['PYTHONPATH'].split(':') if '--dev' in os.environ.get('VEE_EXEC_ARGS', '') else [],

        # Place us into the global applications folder if in vee.
        'bundle_path': (
            os.path.join(os.environ['VEE'], 'Applications', 'SGActions.app')
            if 'VEE' in os.environ else
            'build/lib/sgactions/platforms/darwin/SGActions.app'
        ),
        'plist_defaults': {
            # 'LSBackgroundOnly': True, # Don't show up in dock.
        }

    }],

    scripts=[
        'sgactions/browsers/native/sgactions-native-messenger',
    ],

    classifiers=[
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 2',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
)
