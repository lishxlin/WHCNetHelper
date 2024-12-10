from setuptools import setup, find_packages


setup(
	name='whcnethelper',
	version='0.0.1',
	description='A Python client for Wuhan College network assistance: automated login, keep-alive checks, and script execution.',
	author='Li ShXlin',
	author_email='',
	url='',
	license='LGPLv3',
	packages=find_packages(),
	classifiers=[
		'Development Status :: 2 - Pre-Alpha',
		'Environment :: Console',
		'Intended Audience :: System Administrators',
		'License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)',
		'Natural Language :: English',
		'Operating System :: POSIX :: Linux',
		'Topic :: Internet',
		'Topic :: System :: Networking',
		'Topic :: Utilities',
		'Programming Language :: Python :: Implementation',
		'Programming Language :: Python :: 3',
		'Programming Language :: Python :: 3.12',
	],
	install_requires=[
	],
	entry_points={
		'console_scripts': [
			'whcnethelper=whcnethelper.HelperMain:main',
		],
	},
)
