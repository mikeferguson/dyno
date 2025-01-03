from setuptools import setup

package_name = 'dyno'
setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Michael Ferguson',
    maintainer_email='mfergs7@gmail.com',
    description='Dyno interface and tools',
    license='GPL',
)
