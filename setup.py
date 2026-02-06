from setuptools import find_packages, setup

HYPEN_E_DOT='-e .'

def get_requirements(file_path:str):
    '''
    Docstring for get_requirements
    
    :param file_path: Description
    :type file_path: str
    :return: Description
    :rtype: List[str]
    '''
    requirements=[]
    with open(file_path) as file_obj:
        requirements=file_obj.readlines()
        requirements=[req.replace('\n','') for req in requirements]
        
        if HYPEN_E_DOT in requirements:
            requirements.remove(HYPEN_E_DOT)
    return requirements
        

setup(
    name='mlproject',
    version='0.0.1',
    author='Suman',
    author_email='sumanghosh8767@gmail.com',
    packages=find_packages(),
    install_requires=get_requirements('requirements.txt')
)