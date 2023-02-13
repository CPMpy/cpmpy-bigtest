import argparse
import brotli
from termcolor import colored
import subprocess
import os

def solver_runner(python_path, fileName, folderPath, timeout=60, solver=None): # runs the python examples
    if os.name == 'posix':
        command = "cd " + folderPath + " ; " + "timeout -s SIGKILL " + str(timeout) + "s " + str(
            python_path) + ' ' + str(folderPath) + "/" + str(fileName)
    else:
        command = "cd " + folderPath + " & " + str(python_path) + ' "' + str(folderPath) + "/" + str(fileName)

    print(colored(command, "yellow"))

    p = subprocess.Popen(command, shell=True, stderr=subprocess.PIPE)
    terminal_output = p.stderr.read().decode()

    print(terminal_output)

def findAllPyExamples(path): # creates list of tuples of the python examples' filename, directory
    filelist = []
    for directory, dirs, filenames in os.walk(path):
        for filename in filenames:
            if not filename.endswith(".py"):
                continue
            if filename.__contains__("Pickled"):
                continue
            if filename.__contains__(".bt"):
                continue
            filelist.append((filename, directory))
    return filelist

def getModels():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pyExamples', type=str, help='The path to all python CPMpy examples')
    arguments = parser.parse_args()
    if arguments.pyExamples is None:
        print("Please add the path to the python CPMpy examples using '--pyExamples PATH'.")
        exit(0)

    count = 0
    for nameOfFile, filePath in findAllPyExamples(arguments.pyExamples):
        solver_runner("python3.8", nameOfFile, filePath)  # generates pickle with the modified CPMpy
        print(str(count + 1) + "/" + str(len(filePath)) + "testing: " + str(arguments.pyExamples) + "/ " + str(nameOfFile.replace(".py", "")))

        for f_name in os.listdir(filePath):
            if f_name.startswith("Pickled"):
                oldName = str(filePath) + "/" + str(f_name) # rename pickled file to the name of the example
                newName = str(filePath) + "/" + nameOfFile.replace(".py", "") + str(f_name.replace("Pickled", ""))
                os.replace(oldName, newName)

                with open(newName, "rb") as a: # compress model
                    pdata = a.read()
                    with open(arguments.pyExamples + "/" + newName + '.bt', 'wb') as b:
                        b.write(brotli.compress(pdata))
        count += 1
