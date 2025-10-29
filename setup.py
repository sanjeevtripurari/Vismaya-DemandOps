#!/usr/bin/env python3
"""
Setup script for Vismaya DemandOps Agentic AI System
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

# Read requirements
requirements_file = Path(__file__).parent / "requirements.txt"
requirements = []
if requirements_file.exists():
    with open(requirements_file, 'r', encoding='utf-8') as f:
        requirements = [
            line.strip() 
            for line in f 
            if line.strip() and not line.startswith('#') and not line.startswith('-r')
        ]

setup(
    name="vismaya-demandops-agentic",
    version="1.0.0",
    description="Agentic AI System for AWS Cost Management and Resource Optimization",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Vismaya DemandOps Team",
    author_email="team@vismaya.com",
    url="https://github.com/vismaya/demandops-agentic",
    
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    
    python_requires=">=3.9",
    install_requires=requirements,
    
    extras_require={
        "dev": [
            "black>=23.12.0",
            "isort>=5.13.0",
            "flake8>=7.0.0",
            "pylint>=3.0.0",
            "pytest>=7.4.0",
            "pytest-asyncio>=0.23.0",
            "pytest-cov>=4.1.0",
            "mypy>=1.8.0",
        ],
        "docs": [
            "sphinx>=7.2.0",
            "sphinx-rtd-theme>=2.0.0",
            "myst-parser>=2.0.0",
        ],
        "test": [
            "pytest>=7.4.0",
            "pytest-asyncio>=0.23.0",
            "pytest-mock>=3.12.0",
            "pytest-cov>=4.1.0",
            "pytest-xdist>=3.5.0",
        ]
    },
    
    entry_points={
        "console_scripts": [
            "vismaya-migrate=agentic.migration.enable_all_features:main",
            "vismaya-demo=demo_migration:main",
        ],
    },
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Systems Administration",
        "Topic :: Office/Business :: Financial",
    ],
    
    keywords=[
        "aws", "cost-management", "ai", "agents", "automation", 
        "cloud", "finops", "devops", "machine-learning"
    ],
    
    project_urls={
        "Bug Reports": "https://github.com/vismaya/demandops-agentic/issues",
        "Source": "https://github.com/vismaya/demandops-agentic",
        "Documentation": "https://demandops-agentic.readthedocs.io/",
    },
    
    include_package_data=True,
    zip_safe=False,
)