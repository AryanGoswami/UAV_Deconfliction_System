from setuptools import find_packages, setup

package_name = 'deconfliction_sys'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='iam-aryang',
    maintainer_email='iam-aryang@todo.todo',
    description='TODO: Package description',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            "two_d_decon_sys = deconfliction_sys.two_d_decon_sys:main"
        ],
    },
)
