from setuptools import find_packages, setup

VERSION = "0.6.2"

setup(
    name="rcode",
    version=VERSION,
    description="vscode remode code .",
    keywords="python vscode",
    author="chvolkmann, yihong0618",
    author_email="zouzou0208@gmail.com",
    url="https://github.com/yihong0618/code-connect",
    packages=find_packages(),
    include_package_data=True,
    zip_safe=True,
    install_requires=["sshconf"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries",
    ],
    entry_points={
        "console_scripts": ["rcode = rcode.rcode:main", "rcursor = rcode.rcode:cmain"],
    },
)
