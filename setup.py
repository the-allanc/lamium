import setuptools

setup_params = dict(
    name='lamium',
    version='0.1',
    url = 'https://yougov.kilnhg.com/Code/Repositories/G/panda',
    author="Allan Crooks",
    author_email='allan.crooks@sixtyten.org',
    install_requires=[
        "requests",
        "six",
    ],
    py_modules=['lamium'],
)

if __name__ == '__main__':
    setuptools.setup(**setup_params)
