import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="aquaero-exporter",
    version="0.0.1",
    author="Andrei Costescu",
    author_email="andrei@costescu.no",
    description="Prometheus exporter for Aquaero devices",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/cosandr/aquaero-exporter",
    packages=["aquaero_exporter"],
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.5',
    install_requires=[
        'pyquaero',
    ],
    entry_points={
        'console_scripts': [
            'aquaero-exporter=aquaero_exporter.exporter:main',
        ],
    },
)
