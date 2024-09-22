from setuptools import setup, find_packages

setup(
    name="rorm-py",
    version="1.0.0",
    author="刘虎",
    author_email="huxiaoheigame@gmail.com",
    description="A simple ORM cache library for redis",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url="https://github.com/huxiaohei/rorm-py",  # 项目的主页
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9',
    install_requires=[
        "annotated-types == 0.7.0",
        "pydantic == 2.8.2",
        "pydantic_core == 2.20.1",
        "redis == 5.0.7",
        "setuptools == 75.1.0",
        "typing_extensions == 4.12.2"
    ],
    license="MIT"
)
