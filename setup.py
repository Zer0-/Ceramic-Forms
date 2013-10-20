from setuptools import setup

requires = [
]

setup(
    name='ceramic_forms',
    version='0.0',
    description='Creation of small, extendable web components.',
    classifiers=[
        "Programming Language :: Python",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='Philipp Volguine',
    author_email='phil.volguine@gmail.com',
    packages=['ceramic_forms'],
    include_package_data=True,
    install_requires=requires,
)
