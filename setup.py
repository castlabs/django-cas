#!/usr/bin/env python

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    author='Brodie Rao',
    author_email='brodie.rao@cpcc.edu',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Framework :: Django',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Topic :: Internet :: WWW/HTTP',
    ],
    description='CAS 1.0/2.0 authentication backend for Django',
    keywords='django cas cas2 authentication middleware backend',
    license='MIT',
    name='django_cas',
    packages=['django_cas'],
    url='http://code.google.com/p/django-cas/',
    version='2.0',
)
