import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="awssamdeployer",
    version="0.0.1",
    author="samvanovermeire",
    author_email="sam.van.overmeire@gmail.com",
    description="Helper for deploying AWS SAM projects",
    long_description=long_description,
    url="https://github.com/VanOvermeire/aws-sam-deployer",
    packages=setuptools.find_packages(exclude=["tests.*", "tests"]),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        'PyMonad >= 1.3'
    ]
)
