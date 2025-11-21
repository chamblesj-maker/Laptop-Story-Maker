"""
StoryApp Setup Script
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="storyapp",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-powered novel writing system with local LLMs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/storyapp",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "pyyaml>=6.0",
        "requests>=2.31.0",
        "chromadb>=0.4.22",
        "sentence-transformers>=2.3.1",
        "click>=8.1.7",
        "rich>=13.7.0",
    ],
    entry_points={
        "console_scripts": [
            "storyapp=storyapp:main",
        ],
    },
)
