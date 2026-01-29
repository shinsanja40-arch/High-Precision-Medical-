"""
Setup script for Medical Diagnosis System
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name="medical-diagnosis-system",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Real-time Referee-Mediated Medical Diagnosis System with Circular Overlap Structure",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/medical-diagnosis-system",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Healthcare Industry",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Medical Science Apps.",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "anthropic>=0.25.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "medical-diagnosis=medical_diagnosis_system:main",
        ],
    },
    keywords="medical diagnosis AI multi-agent debate referee healthcare",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/medical-diagnosis-system/issues",
        "Source": "https://github.com/yourusername/medical-diagnosis-system",
    },
)
