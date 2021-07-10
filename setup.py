from setuptools import setup
from COVID19analysis import __version__

with open('Readme.md', 'r') as f:
    readme = f.read()

setup(
    name='COVID19analysis',
    version=__version__,
    packages=['COVID19analysis'],
    url='https://github.com/prasannaba/COVID-19_Analysis_Library',
    license='MIT',
    author='Prasanna',
    python_requires='>=3.7',
    install_requires=['bokeh>=2.3.3', 'panel>=0.11.3', 'pandas<=1.2.5', 'holoviews>=1.14.4',
                      'hvplot>=0.7.2', 'tqdm>=4.61.2'],
    author_email='prasanna.badami@hotmail.com',
    description='COVID19Analysis based on CSSEGISandData on GitHub',
    long_description=readme,
    long_description_content_type='text/markdown',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Mathematics',
        'Topic :: Scientific/Engineering :: Visualization',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Intended Audience :: Developers', 
        'Intended Audience :: Science/Research', 
        'Intended Audience :: Information Technology',
        'Intended Audience :: Financial and Insurance Industry'
    ],
)
