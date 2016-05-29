try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='dewi-boatd-driver',
    version='0.1.0',
    author='Louis Taylor',
    author_email='louis@kragniz.eu',
    description=('Driver to run boatd on dewi'),
    license='GPLv3',
    keywords='boat sailing boatd',
    url='https://github.com/abersailbot/dewi-boatd-driver',
    modules=['dewi_boatd_driver.py'],
)
