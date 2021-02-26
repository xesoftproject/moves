import glob
import os
import typing

import setuptools


with open('README.md', 'r') as fh:
    long_description = fh.read()


def moves_package_data() -> typing.List[str]:
    cwd = os.getcwd()
    os.chdir('moves')
    try:
        static = glob.glob('web/static/**', recursive=True)
        templates = glob.glob('web/templates/**', recursive=True)
        return static + templates
    finally:
        os.chdir(cwd)


setuptools.setup(name='moves',
                 version='0.0.1',
                 author='Vito De Tullio',
                 author_email='vito.detullio@gmail.com',
                 description='the server that handles the moves',
                 long_description=long_description,
                 long_description_content_type='text/markdown',
                 url='https://github.com/xesoftproject/moves',
                 packages=setuptools.find_packages(),
                 python_requires='>=3.8',
                 entry_points={
                     'console_scripts': [
                         'moves-web = moves.web:main',
                         'moves-rest = moves.rest:main',
                         'moves-chat = moves.chat:main'
                     ]
                 },
                 install_requires=[
                     'stomp.py',
                     'chess',
                     'quart-trio',
                     'trio-typing',
                     'hypercorn',
                     'quart-cors',
                     'trio_asyncio',
                     'jsonlines',
                     'PyAudio',
                     'pocketsphinx',
                     'SpeechRecognition',
                     'mockito'
                 ],
                 package_data={'moves': moves_package_data()})
