from setuptools import setup

# Additional keyword arguments for setup
kwargs = {}

with open('README.md') as f:
    kwargs['long_description'] = f.read()

kwargs['version'] = '0.1'

packages = [
    'whatchanged',
    'whatchanged.tests',
]

package_data = {}

setup(
    name="whatchanged",
    author="Puneeth Chaganti",
    author_email="punchagan@muse-amuse.in",
    url = "https://github.com/punchagan/what-changed",
    packages = packages,
    package_data=package_data,
    entry_points = {
        "console_scripts": [
             "what-changed = whatchanged.main:main",
        ],
    },
    **kwargs
)
