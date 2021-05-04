from setuptools import find_packages
from setuptools import setup

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(name='xesoft_moves',
      version='0.0.1',
      author='Vito De Tullio',
      author_email='vito.detullio@gmail.com',
      description='the server that handles the moves',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://github.com/xesoftproject/moves',
      packages=find_packages(),
      package_data={'': (['localhost.crt', 'localhost.key'] +
                         ['py.typed'] +
                         ['model/am/final.mdl',
                          'model/conf/mfcc.conf',
                          'model/conf/model.conf',
                          'model/graph/disambig_tid.int',
                          'model/graph/Gr.fst',
                          'model/graph/HCLr.fst',
                          'model/graph/phones/word_boundary.int',
                          'model/ivector/final.dubm',
                          'model/ivector/final.ie',
                          'model/ivector/final.mat',
                          'model/ivector/global_cmvn.stats',
                          'model/ivector/online_cmvn.conf',
                          'model/ivector/splice.conf',
                          'model/README'])},
      python_requires='>=3.8',
      entry_points={
          'console_scripts': ['moves-rest = moves.rest:main']
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
          'mockito',
          'vosk'
      ])
