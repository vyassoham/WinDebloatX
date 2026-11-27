from setuptools import setup, find_packages

setup(
    name="windebloatx",
    version="2.0.0",
    author="vyassoham",
    url="https://github.com/vyassoham/WinDebloatX",
    description="Modern Windows 10 & 11 system optimizer, privacy hardener, and debloater",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "customtkinter>=6.0.0",
        "rich>=13.0.0",
        "pillow>=10.0.0",
        "darkdetect>=0.8.0",
    ],
    entry_points={
        "console_scripts": [
            "windebloatx=main:main",
        ],
    },
    classifiers=[
        "Operating System :: Microsoft :: Windows",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
