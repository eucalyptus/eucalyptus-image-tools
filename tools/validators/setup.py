#!/usr/bin/env python

from distutils.core import setup

setup(name='euca_image_validation',
      version='0.2',
      packages=['euca_image_validation',],
      scripts=['euca_image_validate.py',],
      url='https://github.com/eucalyptus/eucalyptus-image-tools',
      author='Jeff Uphoff',
      author_email='juphoff@eucalyptus.com',
      description='Image-validation tools for Eucalyptus',
      license='BSD',
      )
