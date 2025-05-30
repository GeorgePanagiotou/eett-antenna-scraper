from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="eett-antenna-scraper",
    version="1.0.0",
    author="George Panagiotou",
    author_email="ge.panagiotou@gmail.com",
    description="A Python web scraper for extracting antenna data from the Greek EETT website",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/GeorgePanagiotou/eett-antenna-scraper",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "eett-scraper=eett_scraper:main",
        ],
    },
    keywords="scraper, web-scraping, eett, antennas, greece, telecommunications",
    project_urls={
        "Bug Reports": "https://github.com/GeorgePanagiotou/eett-antenna-scraper/issues",
        "Source": "https://github.com/GeorgePanagiotou/eett-antenna-scraper",
    },
)
