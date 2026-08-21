# Meant to be run from the root directory of the repo.

# Requirements: * Python 3.7 or higher (to run miniwdl)
#               * Java (to run womtool)
#               * miniwdl: https://github.com/chanzuckerberg/miniwdl
#               * womtool: https://github.com/broadinstitute/cromwell  

import subprocess
import datetime
import sys
import os

skip_syntax_check = False
_failed_ = False

def check_workflow(wf_name, subprocess_array):
	tempfile = open("temp.txt", "w")
	print("[%s] Run %s via miniwdl" % (datetime.datetime.now(), wf_name))
	try:
		subprocess.check_call(subprocess_array,
		stdout=subprocess.DEVNULL, stderr=tempfile)
	except subprocess.CalledProcessError as oops:
		tempfile.close()
		print("ERROR - womtool returned %s" % oops.returncode)
		with open("miniwdl_errors.txt", "a") as stderrfile:
			stderrfile.write("----- Error in %s ------" % this_test)
			with open("temp.txt", "r") as captured_output:
				for line in captured_output:
					stderrfile.write(line)
		_failed_ = True
	tempfile.close()

def syntax_check(womtool_path: str):
	assert os.path.isfile(womtool_path), f"User specified womtool is {womtool_path} but there is no file there"
	print("[%s] Check syntax via womtool..." % datetime.datetime.now())
	for root, dirs, files in os.walk(".", topdown=True):
		for file in files:
			if file.endswith(".wdl"):
				this_wdl = os.path.join(root, file)
				print("[%s] Checking %s..." % (datetime.datetime.now(), this_wdl))
				try:
					subprocess.check_call(["java", "-jar", womtool_path,
					 "validate", "%s" % this_wdl], stdout=subprocess.DEVNULL)
				except subprocess.CalledProcessError as oops:
					# womtool will print more useful stderr to command line
					print("ERROR - womtool returned %s" % oops.returncode)
					_failed_ = True

	print("[%s] Finished syntax check." % datetime.datetime.now())
	if _failed_ == True:
		print("Syntax errors detected. Not running any further tests.")
		quit()

def cleanup_miniwdl_extras():
	print("Cleaning up...")
	month_with_zero = datetime.datetime.strftime(datetime.datetime.now(), "%m")
	day_with_zero = datetime.datetime.strftime(datetime.datetime.now(), "%d")
	today = "".join([str(datetime.datetime.now().year), month_with_zero, day_with_zero])
	if os.path.basename(os.getcwd()) != "checker-WDL-templates":
		print("You don't seem to be in the expected directory. Just in case, miniwdl files will not be cleaned up.")
	else:
		os.system("rm -rf %s*" % today)

def main(womtool_path: str):
	if not skip_syntax_check:
		syntax_check(womtool_path)
	print("Checking workflows...")
	print("Not checking check_task_outputs, as its inputs are not local...")

	check_workflow("fuzzycheck", ["miniwdl", "run", "check_approximately_equals/fuzzycheck_RData.wdl",
		 "testRDatafile=test_data/allele_chr1.RData",
		 "truthRDatafile=test_data/truths/allele_chr1.RData",
		 "testRDataarray=test_data/allele_chr1.RData",
		 "testRDataarray=test_data/allele_chr2.RData",
		 "truthRDataarray=test_data/truths/allele_chr1.RData",
		 "truthRDataarray=test_data/truths/allele_chr2.RData"])

	check_workflow("outputs_all_required base case", 
		["miniwdl", "run", "check_wf_outputs/outputs_all_required/parent_req.wdl",
		"file1=test_data/allele_chr1.RData",
		"file2=test_data/truths/allele_chr1.RData",
		"file3=test_data/allele_chr1.RData"])

	check_workflow("outputs_all_required checker case",
		["miniwdl", "run", "check_wf_outputs/outputs_all_required/template_req.wdl",
		"file1=test_data/NWD176325.005percent.recab.crai",
		"file2=test_data/NWD119836.0005.recab.cram.crai",
		"file3=test_data/NWD119836.0005.recab.crai",
		"singleTruth=test_data/truths/NWD176325.005percent.recab.crai.txt",
		"truthSet=test_data/truths/NWD119836.0005.recab.cram.crai.txt",
		"truthSet=test_data/truths/NWD119836.0005.recab.crai.txt"])


	check_workflow("outputs_some_optional base case",
		["miniwdl", "run", "check_wf_outputs/outputs_some_optional/parent_opt.wdl",
		"optionalInput=test_data/NWD119836.0005.recab.cram.crai",
		"requiredInput=test_data/NWD176325.005percent.recab.crai"])

	check_workflow("outputs_some_optional checker case",
		["miniwdl", "run", "check_wf_outputs/outputs_some_optional/template_opt.wdl",
		"optionalInput=test_data/NWD119836.0005.recab.cram.crai",
		"requiredInput=test_data/NWD176325.005percent.recab.crai",
		"singleTruth=test_data/truths/foo.txt",
		"arrayTruth=test_data/truths/bar.txt",
		"arrayTruth=test_data/truths/second_bar/bar.txt",
		"arrayTruth=test_data/truths/foo.txt"])

	if _failed_:
		print("At least one workflow failed.")

	cleanup_miniwdl_extras()

if __name__ == "__main__":
	if len(sys.argv) != 2:
		print("Usage: python tests/tests.py [womtool_jar]")
		print("Assumptions: ")
		print(" * Java is on the path")
		print(" * test_data/ folder from repo is in workdir (i.e. you're running this from the root of the repo")
		print(" * miniwdl was pip-installed such that `miniwdl` command is on the path")
		sys.exit(1) # not zero, so this can be caught in CICD
	else:
		womtool_path = sys.argv[1]
		if not womtool_path.endswith(".jar"):
			print("womtool doesn't have .jar extension? Make sure you to specify the jar itself, not only the path leading up to it")
			sys.exit(1)
		main(womtool_path)


