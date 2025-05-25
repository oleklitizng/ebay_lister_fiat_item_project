# ebay_lister_fiat_item_project/setup.py

from setuptools import setup, find_packages
import os

# Function to read the long description from README.md
def read_long_description():
    try:
        with open(os.path.join(os.path.dirname(__file__), "README.md"), encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "eBay Lister Package - see repository for details."

setup(
    name="ebay_lister_pkg",  # Replace with your desired package name on PyPI if you publish
    version="0.1.0",
    author="Ole von Klitzing",  # Replace with your name
    author_email="ovonklit@uni-bremen.de",  # Replace with your email
    description="A package to list auto parts on eBay, with EPER integration and GUI.",
    long_description=read_long_description(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ebay_lister_fiat_item_project",  # Replace with your project's URL
    packages=find_packages(where=".", include=['ebay_lister_fiat_item', 'ebay_lister_fiat_item.*']),
    classifiers=[
        "Development Status :: 3 - Alpha", # Or "4 - Beta", "5 - Production/Stable"
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",  # Choose your license
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: OS Independent",
        "Topic :: Office/Business :: Financial :: Point-of-Sale",
        "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    ],
    python_requires=">=3.8", # Minimum Python version
    install_requires=[
        "python-dotenv>=0.15.0",
        "ebaysdk>=2.2.0",        # As used in ebay_item.py
        "customtkinter>=5.0.0",  # As used in gui.py
        "requests>=2.25.0",      # As used in scrape_open_eper.py
        "beautifulsoup4>=4.9.0", # As used in scrape_open_eper.py
        "cloudscraper>=1.2.58",  # As used in scrape_open_eper.py
        # Add any other direct dependencies here
    ],
    extras_require={
        "dev": [
            "pytest>=6.0",      # For running tests (alternative to unittest)
            "flake8>=3.8",      # For linting
            "black>=20.8b1",    # For code formatting
            "mypy>=0.900",      # For static type checking
            "twine>=3.0.0",     # For uploading to PyPI
            "wheel",            # For building wheel distributions
        ],
        "test": [
            "pytest>=6.0",
            # "pytest-cov", # For coverage
        ]
    },
    entry_points={
        "console_scripts": [
            "ebay-lister-gui=ebay_lister_fiat_item.gui:main_gui_app", # Assuming you create a main_gui_app function in gui.py
        ],
    },
    project_urls={ # Optional
        "Bug Tracker": "https://github.com/oleklitizng/ebay_lister_fiat_item_project/issues",
        "Source Code": "https://github.com/oleklitizng/ebay_lister_fiat_item_project",
    },
    # include_package_data=True, # If you have non-Python files inside your package to include
    # package_data={
    #     'your_package_name': ['path/to/data_file.dat'],
    # },
)