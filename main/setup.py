import setuptools
import toml
import os
from file_system_py import iterate_paths_in

folder =  os.path.abspath(os.path.dirname(__file__))
# 
# get the data out of the toml file
# 

toml_info = toml.load(f"{folder}/../pyproject.toml")
package_info = {**toml_info["tool"]["poetry"], **toml_info["tool"]["extra"]}

# 
# get the data out of the readme file
# 
with open(f"{folder}/../README.md", "r") as file_handle:
    long_description = file_handle.read()

packge_path = f"""{folder}/{package_info["name"]}"""
names = [
    each[len(packge_path)+1:]
        for each in iterate_paths_in(packge_path, recursively=True)
            if os.path.isfile(each) and not each.endswith(".pyc") and not any([ sub_name in each for sub_name in ['/settings/.cache','/settings/during_clean','/settings/during_manual_start','/settings/during_purge','/settings/during_start','/settings/during_start_prep','/settings/extensions','/settings/home','/settings/requirements','/settings/fornix_core',] ])
]

# 
# generate the project
#  
setuptools.setup(
    name=package_info["name"],
    version=package_info["version"],
    description=package_info["description"],
    url=package_info["url"],
    author=package_info["author"],
    author_email=package_info["author_email"],
    license=package_info["license"],
    packages=[package_info["name"]],
    install_requires=[
    ],
    setup_requires=['file_system_py', 'toml'],
    include_package_data=True,
    package_data={
        package_info["name"]: names,
    },
    classifiers=[
        # examples:
        # 'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Programming Language :: Python',
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires='>=3.6',
)