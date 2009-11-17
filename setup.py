from distutils.core import setup
import os

from pyunsrc.version import VERSION

setup(
  name='Pyun', 
  author='Eyal Lotem',
  author_email='eyal.lotem@gmail.com',
  license='The GNU General Public License 2 and above',
  version=VERSION,
  packages=['pyunsrc'],
  scripts=['pyun.py'],
)
