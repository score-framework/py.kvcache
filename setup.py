import os

from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()

setup(
    name='score.kvcache',
    version='0.2.1',
    description='Key/Value cache of The SCORE Framework',
    long_description=README,
    author='strg.at',
    author_email='support@strg.at',
    url='http://strg.at',
    keywords='web wsgi caching',
    packages=['score', 'score.kvcache'],
    namespace_packages=['score'],
    license='LGPL',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Environment :: Web Environment',
        'Framework :: Pyramid',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Lesser General '
            'Public License v3 or later (LGPLv3+)',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Application Frameworks',
    ],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'score.init >= 0.3.1',
    ],
)
