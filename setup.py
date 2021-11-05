from setuptools import find_packages, setup

with open("README.md", encoding="utf-8") as f:
    # just use the whole README.md as the long description -- if it ever comes about
    # that we distribute on pypi, it's useful to see all this on the project page.
    long_desc = f.read()

setup(
    name="snowballgr-api",
    version="1.0.0",
    description="Snowball General Release Application",
    long_description=long_desc,
    url="https://github.com/duke-crucibe/snowballgr-api",
    author="Jenny Wang",
    author_email="jenny.wang254@duke.edu",
    packages=find_packages(where="src"),  # see https://blog.ionelmc.ro/2014/05/25/python-packaging/
    package_dir={'': 'src'},
    python_requires=">=3.8",
    zip_safe=False,
)
