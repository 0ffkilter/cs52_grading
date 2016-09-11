import os, subprocess
from threading import Timer

input_string = "c to continue, r to rerun, o to open file (in Nano), e to exit \n"
timeout = 15

def run_file(student, grading):
    """
    Run a file through the grading script
    Runs shell command 'cat pregrade.sml asgtN.sml grading_script.sml | sml'

    student:        File to run
    grading:        Grading script to compare against

    Return Value: output of sml command
    """
    pregrade = os.path.join(os.getcwd(), "pregrade.sml")
    #cmd = r'echo "use \"%s\"; use \"%s\"; use \"%s\";" | sml -Cprint.depth=100, -Cprint.length=1000' %(pregrade, student, grading)
    cmd = r'cat %s %s %s | sml' %(pregrade, student, grading)

    proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    kill_proc = lambda p: p.kill()
    timer = Timer(timeout, kill_proc, [proc])

    try:
        print("starting file")
        timer.start()
        result = proc.communicate()[0].decode("utf-8").splitlines()
    finally:
        timer.cancel()

    for r in result:
        print(r);
    return result

def print_file(file_name, asgt_name):
    cmd = r'lpr %s -K 1 -T %s -p -P %s' %(file_name, asgt_name, 'Edmunds_227')


def parse_folder(folder_directory, assign_num):
    """
    Returns correct assignment directory

    folder_directory:   directory of submission folder
    assign_num:         assignment number

    Return Value:       Path of correct assign directory
    """
    assign_name = "asgt" + "0" if assign_num < 10 else ""
    assign_name += str(assign_num) + "-submissions"
    assign_dir = os.path.join(folder_directory, assign_name)

    return assign_dir


def read_tograde(a_dir):
    """
    Reads the tograde.txt file

    a_dir:          directory of .txt file

    Return Value: list of files
    """

    f = open(os.path.join(a_dir, "tograde.txt"), "r")
    return f.read().splitlines();

def parse_filename(filename):
    """
    Parses the filenames to get id and email out

    filename:       filename to read

    Return Value: (ID, @school.edu, Filename)
    """

    late_txt = ""
    if ("LATE") in filename:
        filename = filename[:-6].strip()
        late_txt = " LATE SUBMISSION"
    name = filename[filename.find("Z")+2:]
    idx = name.find("@")
    return (name[:idx] + late_txt, name[idx:], filename)

def start_early(start_with, lst):
    """
    Truncates list of files early if grading isn't starting at first alphabetical file

    start_with:     String to compare against
    lst:            list of filenames

    Return Value:   Modified list of filenames
    """

    if start_with == "":
        return lst
    idx = 0
    for i in range(len(lst)):
        if lst[i][0].startswith(start_with):
            break
    if not i == len(lst) - 1:
        return lst[i:]

    return lst

def open_file(filename):
    """
    Open a file in Nano

    filename:       filename to open

    Return Value:   none
    """

    subprocess.call(["nano", filename])

