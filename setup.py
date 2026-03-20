from setuptools import setup, find_packages

setup(
    name="lingflow",
    version="3.2.0",
    description="多智能体工作流引擎 - 灵通工作流",
    author="Guangda",
    packages=find_packages(),
    install_requires=[
        "pyyaml>=6.0",
        "click>=8.0",
    ],
    extras_require={
        "server": ["flask>=2.0"],
        "dev": ["pytest", "pytest-asyncio"],
    },
    entry_points={
        "console_scripts": [
            "lingflow=cli:cli",
        ],
    },
    python_requires=">=3.8",
)
