from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="openclaw-jev-guard",
    version="0.1.0",
    author="OpenClaw Contributors",
    description="Verification layer for AI agents using Jev structured decision-making",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/openclaw-jev-guard",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "anthropic>=0.25.0",
        "httpx>=0.25.0",
        "pyyaml>=6.0",
        "python-dotenv>=1.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-asyncio>=0.20.0",
            "black>=23.0",
            "isort>=5.0",
            "mypy>=1.0",
            "flake8>=6.0",
        ],
        "docs": [
            "sphinx>=5.0",
            "sphinx-rtd-theme>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "openclaw-validator=jev_decision_maker.cli:main",
        ],
    },
)
