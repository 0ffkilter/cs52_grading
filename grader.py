#!/usr/bin/env python3
from __future__ import print_function
import sys
import subprocess
import os
import os.path as path
import argparse
from argparse import RawTextHelpFormatter
from grader_utils import *
from grading_scripts import student_list
import re
from datetime import datetime

DEFAULT_TIMEOUT = 3
TIMEOUT = DEFAULT_TIMEOUT

def grade_print(assign_num, folder_directory, s_with, s_next):
    """
    Print an assignment

    assign_num:         number of assignment (integer)
    folder_directory:   directory that assignment FOLDER is located in (where the submission folder is)
    start_with:         partial or complete username to start grading at
    """

    assign_dir = parse_folder(folder_directory, assign_num)


    #Standardize file name of assignment submission
    file_name = "asgt" + "0" if assign_num < 10 else ""
    file_name += str(assign_num) + ".sml"

    #Target directory name
    target_name = "asgt" + "0" if assign_num < 10 else ""
    target_name += str(assign_num) + '-ready'

    #get list of files
    miss_list, files = extract_files(assign_dir, SUFFIX, file_name, target_name)

    #Trim list of files if starting not at the beginning
    if s_next != "":
        files = start_next(s_next, files, 1)
    elif s_with != "":
        files = start_early(s_with, files)

    if len(miss_list) != 0:
        raw_input("Enter to continue")

    for (name, f_name) in files:
       print_file(os.path.join(target_name, f_name), file_name)


def grade(f_name, grading_files, num_pat, silent=False, round_to=0.25, f_dir=os.getcwd()):
    global TIMEOUT, DEFAULT_TIMEOUT
    grading_pre, style_points, total_points = grading_files[0]
    grading_scripts = grading_files[1:]

    ret_dictionary = {}

    passed = 0
    failed = 0
    halted = 0
    total_deduction = 0

    (too_long, tabs, comments, total) = format_check(f_name)

    deduct_list = []

    ret_string = ""
    for (f_script, points, tests) in grading_scripts:
        print("running file: %s" %(f_script))
        (r, err) = run_file(f_dir, f_name, grading_pre, f_script, timeout=TIMEOUT)

#        if res ==  "ERR":
#            ret_string = ret_string + "Error reached\n"
#            ret_string = ret_string + "Traceback: \n" + "\n".join(r.splitlines()[-TRACEBACK_LENGTH:])
        idx = r.find("--START--")
        res = r[r.find("--START--")+9:r.find("--END-")]
        if idx != -1:
            ret_string = ret_string + res + "\n"
        else:
            ret_string = ret_string + "error before test"

        c_pass = r.count(" PASS")
        c_fail = r.count(" FAIL")
        c_halt = int(tests) - c_pass - c_fail

        if (c_halt > 0):
            ret_string = ret_string + "Test timed out\n\n"
            any_timeout = True


        passed += c_pass
        failed += c_fail
        halted += c_halt

        points = float(points)
        tests = int(tests)

        c_deduction = deduct_points(points, tests, c_pass, c_fail, c_halt)

        if (c_deduction > 0):
            try:
                deduct_list.append((re.findall(num_pat, f_script)[0], c_deduction))
            except:
                deduct_list.append((re.findall("asgt06_(.*).52", f_script)[0], c_deduction))

        total_deduction += c_deduction

        if c_deduction > 0:
            ret_string = ret_string + str(c_deduction) + " points taken off on previous problem\n\n"

    style_deduction = 0
    style_multiplier = 1.0

    if too_long > 20:
        style_multiplier = 0.9
    if tabs > 0:
        style_deduction += 0.5
    if comments < len(grading_scripts) + 2:
        style_deduction += 0.5
    if comments < len(grading_scripts)/2 and style_deduction == 1.5:
        style_deduction += 0.5


    ret_string = "\n".join([i for i in ret_string.split("\n") if not "tmp.sml" in i])
    ret_dictionary["ret_string"] = ret_string
    ret_dictionary["tests_passed"] = passed
    ret_dictionary["tests_failed"] = failed
    ret_dictionary["tests_halted"] = halted
    ret_dictionary["tests_total"] = passed + failed + halted
    ret_dictionary["num_long"] = too_long
    ret_dictionary["num_tabs"] = tabs
    ret_dictionary["num_comments"] = comments
    ret_dictionary["style_points"] = int(style_points)
    ret_dictionary["total_points"] = int(total_points)
    ret_dictionary["style_deduction"] = style_deduction
    ret_dictionary["style_multiplier"] = style_multiplier
    ret_dictionary["correct_deduction"] = total_deduction
    ret_dictionary["deduct_list"] = deduct_list
    ret_dictionary["suggested_score"] = roundPartial((ret_dictionary["total_points"] - ret_dictionary["style_deduction"] -
    ret_dictionary["correct_deduction"]) * ret_dictionary["style_multiplier"], round_to)

    return ret_dictionary

def print_results(results, silent=False):
    print_string = ""
    print_string = print_string + (results["ret_string"])

    print_string = print_string + ("====Summary====\n")

    print_string = print_string + ("")

    print_string = print_string + "\n" + ("Tests:")
    print_string = print_string + "\n" + ("Passed: " + str(results["tests_passed"]))
    print_string = print_string + "\n" + ("Failed: " + str(results["tests_failed"]))
    print_string = print_string + "\n" + ("Halted: " + str(results["tests_halted"]))
    print_string = print_string + "\n" + ("Total:  " + str(results["tests_total"]))

    print_string = print_string + "\n" + ("")

    print_string = print_string + "\n" + ("Style:")
    print_string = print_string + "\n" + ("# Characters: " + str(results["num_long"]))
    print_string = print_string + "\n" + ("# Tabs:       " + str(results["num_tabs"]))
    print_string = print_string + "\n" + ("# Comments:   " + str(results["num_comments"]))

    print_string = print_string + "\n" + ("")

    print_string = print_string + "\n" + ("Correctness Deductions:")
    print_string = print_string + "\n" + ("Num | Deduction")
    for (n, g) in results["deduct_list"]:
        print_string = print_string + "\n" + (n.ljust(4) + "|" + str(g).rjust(4))

    print_string = print_string + "\n" + ("")

    style_points = results["style_points"] - results["style_deduction"]
    correct_points = results["total_points"] - results["style_points"] - results["correct_deduction"]
    correct_points_total = results["total_points"] - results["style_points"]

    print_string = print_string + "\n" + ("Totals:")
    print_string = print_string + "\n" + ("Style Points:       " + str(style_points) + "/" + str(results["style_points"]))
    print_string = print_string + "\n" + ("Correctness Points: " + str(correct_points) + "/" + str(correct_points_total))
    if results["style_multiplier"] != 1:
        print_string = print_string + "\n" + ("Style Multiplier:   " + str(results["style_multiplier"]))

    print_string = print_string + ("")

    if not silent:
        print(print_string)
        print("Suggested Score:    " + str(results["suggested_score"]))


    print_string = print_string + ("\n\n\n====Grader Comments====")
    print_string = print_string + ("\n\n\n\n\n\n\n\n\n\n")
    print_string = print_string + ("Final Score:  /" + str(results["total_points"]))

    return print_string




def grade_file(assign_num, f_name, round_to=0.5):
    """
    Grade one file

    assign_num:         assignment number
    f_name:             name of file to grade
    """

    assign_name = "asgt" + "0" if assign_num < 10 else ""
    assign_name += str(assign_num)

    num_pat = assign_name + "_(.*).sml"

    #Standardize file name of assignment submission
    file_name = assign_name + ".sml"

    grading_list_file = open(os.path.join(os.getcwd(), "grading_scripts", assign_name, (assign_name + "_lst.txt")), 'rU')
    grading_files = grading_list_file.read().split("\n")

    grading_files = [parse_pre_line(os.path.join(os.getcwd(), "grading_scripts", assign_name, f)) for f in grading_files]

    result = grade(f_name, grading_files, num_pat)
    to_file = print_results(result)


def grade_assign(assign_num, folder_directory, s_with, s_next, silent_grade=False, no_confirm=False, outfile="", round_to=0.5):
    """
    Grade an assignment

    assign_num:         number of assignment (integer)
    folder_directory:   directory that assignment FOLDER is located in (where the submission folder is)
    s_with:         partial or complete username to start grading at

    Return val: none
    """
    global TIMEOUT,DEFAULT_TIMEOUT

    grades = []
    assign_dir = parse_folder(folder_directory, assign_num)

    assign_name = "asgt" + "0" if assign_num < 10 else ""
    assign_name += str(assign_num)


    num_pat = assign_name + "_(.*).sml"
    #Standardize file name of assignment submission
    file_name = assign_name + ".sml"

    grading_list_file = open(os.path.join(os.getcwd(), "grading_scripts", assign_name, (assign_name + "_lst.txt")), 'rU')
    grading_files = grading_list_file.read().split("\n")

    grading_files = [parse_pre_line(os.path.join(os.getcwd(), "grading_scripts", assign_name, f)) for f in grading_files if f is not ""]
    grading_pre, style_points, total_points = grading_files[0]
    grading_scripts = grading_files[1:]

    #Target directory name
    target_name = assign_name + '-ready'

    #get list of student files
    miss_list, files = extract_files(assign_dir, SUFFIX, [file_name], target_name)

    #Trim list of files if starting not at the beginning
    if s_next != "":
        files = start_next(s_next, files, 1)
    elif s_with != "":
        files = start_early(s_with, files)
    if len(miss_list) != 0:
        raw_input("Enter to continue")

    for (name, f_name) in files:
        while True:

            #Print Name
            if not silent_grade:
                print("Name : " + name + "\n")
            else:
                print("=", end="")

            # #Run the file through the script
            result = grade(os.path.join(target_name,name, f_name), grading_files, num_pat, silent_grade, f_dir=os.path.join(os.getcwd(),target_name, name))

            result_str = print_results(result, silent_grade)

            grades.append((name, result["suggested_score"]))

            grade_name = os.path.join(target_name, name, "grades.txt")

            with open(grade_name, "w+") as graded_file:
                graded_file.write(result_str)

            if not no_confirm:
                print(INPUT_STRING)
                inp = raw_input("t: run with longer timeout (60 seconds)" if result["tests_halted"] > 0 else "")

                """
                c: continue (also just pressing enter works)
                r: rerun file (assumed that it's been edited)
                o: open file for editing in Nano
                e: exit
                t: run without timeout (potentially dangerous)
                """

                if (inp.lower() == "t") or inp == "":
                    TIMEOUT=DEFAULT_TIMEOUT
                    break
                elif inp.lower() == "t":
                    TIMEOUT=60
                elif inp.lower() == 'o':
                    open_file(os.path.join(assign_dir, dname, file_name))
                    break
                elif inp.lower() == 'e':
                    sys.exit(0)
                elif inp.lower() == 'r':
                    pass
                else:
                    break
            else:
                break
    if outfile != "":
        o_file = open(outfile, 'w');

        g_sum = 0
        for (n, g) in grades:
            o_file.write("%s : %s\n" %(n, g))
            g_sum += g

        o_file.write("Avg: " + str(g_sum/len(grades)))





def main():
    global TIMEOUT, DEFAULT_TIMEOUT
    parser = argparse.ArgumentParser(formatter_class=RawTextHelpFormatter)

    parser.add_argument('--assign-dir', action='store', dest='assign_dir', default=os.getcwd(), type=str, help=
            """
            Where the assign directory is. If no option is specified, it is assumed the folder is in the current directory.
            """)

#     parser.add_argument('--grading-option', action='store', dest='grading_option', default='default', type=str, help=
            # """
            # Which option to choose for grading:

            # default  : grade those in tograde.txt
            # latest   : grade the absolute latest entries, even if late
            # on-time  : only grade the latest on time things

            # """)

    parser.add_argument('--hide-email', action='store', dest='email_silent', default='false', type=bool, help=
            """
            Hide email address when grading, only display the username

            false    : display entire email
            true     : only display username, hide @____.edu

            """)

    parser.add_argument('--assign', action='store', dest='assign_num', default='-1', type=int, help =
            """
            Which assign to grade - as an integer
            """)

    parser.add_argument('--start-with', action='store', dest='start_with', default='', type=str, help=
            """
            Which name to start with (can be partial string)
            """)

    parser.add_argument('--round-to', action='store', dest='round_to', default=0.5, type=float, help=
            """
            How far to round, defaults to 0.25
            """)

    parser.add_argument('-p', action='store_true', help =
            """
            Print flag.  Overrides other actions
            """)

    parser.add_argument('-silent-grade', action='store_true', help =
            """
            Don't print anything
            """)

    parser.add_argument('-no-confirm', action='store_true', help =
            """
            Don't confirm, keep oging after grading
            """)

    parser.add_argument('--outfile', action='store', dest='outfile', default='', type=str, help=
            """
            Where to output grades
            """)

    parser.add_argument('--start-next', action='store', dest='start_next', default='', type=str, help=
            """
            Start the assignment AFTER the one containing the string given.  Can be partial name
            """)

    parser.add_argument('--timeout', action='store', dest='timeout', default=3, type=int, help=
            """
            timeout (in seconds) to wait before force terminating problem
            """)

    parser.add_argument('--traceback-length', action='store', dest='traceback_length', default=6, type=int, help=
            """
            how many lines of error to print
            """)

    parser.add_argument('--run-file', action='store', dest='file', default='', type=str, help=
            """
            Run one specific file.  Should be in the current directory
            """
            )

    res = parser.parse_args()
    print(res.start_with)
    if res.assign_num < 0:
        print("assign number required with --assign")
        sys.exit(0)

    DEFAULT_TIMEOUT=res.timeout
    TIMEOUT=DEFAULT_TIMEOUT
    TRACEBACK_LENGTH=res.traceback_length
    STUDENT_LIST = student_list
    if (res.p):
        grade_print(res.assign_num, res.assign_dir, res.start_with, res.start_next)
    else:
        if (res.file != ""):
            grade_file(res.assign_num, res.file)
        else:
            grade_assign(res.assign_num, res.assign_dir, res.start_with,
                    res.start_next, silent_grade=res.silent_grade, no_confirm=res.no_confirm, outfile=res.outfile, round_to=res.round_to)

if __name__ == "__main__":
    main()
