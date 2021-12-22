
# CPM / C++ Project Manager.

CPM is a high-level Python Command Line Program.
#### Still in a buggy alpha state.

## CPM using required
Python interpreter and Mingw g++/gcc complier
```bash
  python version 3.8 < 3.10
```
## CPM Installation

Install cpm with pip

```bash
  pip install cpp-projects-manager-cli
```
## create c++ project with CPM
```bash
  python -m cpm init <project-name> <directory> !directory is Optional
```
```cmd
     _____   _____    __  __ 
    / ____| |  __ \  |  \/  |
   | |      | |__) | | \  / |
   | |      |  ___/  | |\/| |
   | |____  | |      | |  | |
    \_____| |_|      |_|  |_|
   
          welcome to cpm
   
project author: example  
project description: demo              
project entry point(main.cpp): 
successfully create your example project
```
#### cpm.json
```json
{
    "name": "example",
    "version": "1.0.0",
    "author": "example",
    "description": "demo",
    "entry_point": "main.cpp"
}
```
## run project
```base
  python -m cpm run <c++-file-name> !Optional
```
## How to add C++ App in project
First create c++ app
### create app
```bash
  python -m cpm makeapp <app-name> <directory> !directory is Optional
```
```bash
  $~ python -m cpm makeapp test
  $~ successfully create your test app
```
## app add in cpm.json
open cpm.json file in any text editor. and add c++ app
```json
 {
  ....
  "apps": [
        {
            "name": "test"
        }
    ]
 }
```
again run your project with app
```base
  $~ > python -m cpm run
  [ build ] --- test --- [ D:\......\test.a ] 0.174ms
  combine compile main.cpp
  compile successfully. 0.617ms
  Hello World!
```
## Run new terminal
```base
  $~ > python -m cpm run --new-terminal
  [ build ] --- test --- [ D:\......\test.a ] 0.174ms
  combine compile main.cpp
  compile successfully. 0.617ms
  Hello World!
```

## Custom Command
make folder and file on current work dir:
```
|- extra_commands
|        |
|----- __init__.py
|----- commands
|           |
|--------- __init__.py
|--------- example.py
|- test
|- cpm.json
|- main.cpp
```
#### example.py
```python.py
from cpm.core.base import BaseCommand

class Command(BaseCommand):
    """
    Example command
    """
    help = 'Example command'
    description = 'Example command'
    
    def add_arguments(self, parser):
        parser.add_argument('--example', action='store_true', help='Example argument')

    def handle(self, *args, **options):
        print('Example command', options)
```
#### check custom command
```base
    $~ python -m cpm --help

    Type 'python -m cpm help <subcommand>' for help on a specific subcommand.

    Available subcommands:

    Commands:
       example                 Example command
       init                    Creates a c++ project.
       makeapp                 Creates a c++ app.
       run                     Runs c++ project.
```
#### run custom command
```base
    $~ python -m cpm example
    Example command {'traceback': False, 'example': False}
```
#### Command help
```base
$~ python -m cpm example --help
usage: __main__.py example [--example] [-h] [-v] [--traceback]

Example command

optional arguments:
  --example      Example argument
  -h, --help     show this help message and exit
  -v, --version  Show program's version number and exit.
  --traceback    Raise on CommandError exceptions.
```