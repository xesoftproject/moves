from setuptools import setup, find_packages

with open('README.md', 'r') as fh:
    long_description = fh.read()

setup(name='moves',
      version='0.0.1',
      author='Vito De Tullio',
      author_email='vito.detullio@gmail.com',
      description='the server that handles the moves',
      long_description=long_description,
      long_description_content_type='text/markdown',
      url='https://github.com/xesoftproject/moves',
      packages=find_packages(),
      python_requires='>=3.8',
      entry_points={
          'console_scripts': [
              'moves-web = moves.web:main',
              'moves-rest = moves.rest:main'
          ]
      },
      install_requires=[
          'Flask',
          'stomp.py',
          'python-chess',
          'flask-cors'
      ])
