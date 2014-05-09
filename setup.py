import os

from setuptools import setup, find_packages


data_files = {}
root = os.path.dirname(__file__)
for base in (
    'art',
    'browser_addons',
    'LaunchAgents',
    'Services',
    'Shotgun Action Dispatcher.app',
):
    for dir_path, dir_names, file_names in os.walk(os.path.join(root, base)):
        for file_name in file_names:
            if file_name.startswith('.'):
                continue
            rel_dir = os.path.relpath(dir_path, root)
            rel_path = os.path.join(rel_dir, file_name)
            data_files.setdefault(rel_dir, []).append(rel_path)


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
    
    data_files=data_files.items(),

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
