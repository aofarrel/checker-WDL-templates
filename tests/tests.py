# Meant to be run from the root directory of the repo.

# Requirements: * Python 3.7 or higher (to run miniwdl)
#               * Java (to run womtool)
#               * womtool: https://github.com/broadinstitute/cromwell (you only need womtool, not Cromwell)
#               * miniwdl: https://github.com/chanzuckerberg/miniwdl (must be on path, or run this script in a venv)

# pylint: disable=bad-indentation,consider-using-f-string,line-too-long,missing-module-docstring,trailing-whitespace

import subprocess
import datetime
import sys
import os

def run_workflow(wf_name, subprocess_array):
	"""Runs workflow via miniwdl (instead of Cromwell, because Cromwell is slow locally)"""
	print("[%s] [%s] Running via miniwdl" % (datetime.datetime.now(), wf_name))
	result = subprocess.run(subprocess_array,
		stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True, check=False)
	if result.returncode != 0:
		print("[%s] [%s] ERROR - miniwdl run returned %s" % (datetime.datetime.now(), wf_name, result.returncode))
		with open("miniwdl_errors.txt", "a", encoding="utf-8") as stderrfile:
			stderrfile.write("----- Error in %s ------" % wf_name)
			stderrfile.write(result.stderr)
		return False
	print("[%s] [%s] Passed miniwdl run" % (datetime.datetime.now(), wf_name))
	return True
	
def syntax_check(womtool_jar: str):
	"""Run womtool and miniwdl check on every workflow in the repo"""
	something_failed = False
	print("[%s] Checking syntax via womtool and miniwdl..." % datetime.datetime.now())
	for root, _, files in os.walk(".", topdown=True):
		for file in files:
			if file.endswith(".wdl"):
				if not passes_miniwdl_check(os.path.join(root, file)):
					something_failed = True
				if not passes_womtool_validate(os.path.join(root, file), womtool_jar):
					something_failed = True
	if something_failed is True:
		print("[%s] At least one WDL failed miniwdl check or womtool!" % datetime.datetime.now())
		return False
	print("[%s] Finished syntax checking all WDLs, all have passed" % datetime.datetime.now())
	return True

def passes_miniwdl_check(wdl_to_check: str) -> bool:
	"""Does `miniwdl check wdl_to_check` return 0? (WARNINGS WILL NOT BE SHOWN)"""
	print("[%s] [%s] Checking with miniwdl..." % (datetime.datetime.now(), wdl_to_check))
	try:
		subprocess.check_call(["miniwdl", "check", wdl_to_check], stdout=subprocess.DEVNULL)
	except subprocess.CalledProcessError as oops:
		print("[%s] [%s] ERROR - miniwdl check returned %s" % 
			(datetime.datetime.now(), wdl_to_check, oops.returncode))
		return False
	print("[%s] [%s] Passed miniwdl" % (datetime.datetime.now(), wdl_to_check))
	return True

def passes_womtool_validate(wdl_to_check: str, womtool_jar: str) -> bool:
	"""Does `java -jar womtool_jar validate wdl_to_check` return 0?"""
	print("[%s] [%s] Checking with womtool..." % (datetime.datetime.now(), wdl_to_check))
	try:
		subprocess.check_call(["java", "-jar", womtool_jar,
		 "validate", wdl_to_check], stdout=subprocess.DEVNULL)
	except subprocess.CalledProcessError as oops:
		# womtool will print more useful stderr to command line
		print("[%s] [%s] ERROR - womtool returned %s" % 
			(datetime.datetime.now(), wdl_to_check, oops.returncode))
		return False
	print("[%s] [%s] Passed womtool" % (datetime.datetime.now(), wdl_to_check))
	return True

# this is just too risky to be default behavior
#def cleanup_miniwdl_extras():
#	print("Cleaning up...")
#	month_with_zero = datetime.datetime.strftime(datetime.datetime.now(), "%m")
#	day_with_zero = datetime.datetime.strftime(datetime.datetime.now(), "%d")
#	today = "".join([str(datetime.datetime.now().year), month_with_zero, day_with_zero])
#	if os.path.basename(os.getcwd()) != "checker-WDL-templates":
#		print("You don't seem to be in the expected directory. Just in case, miniwdl files will not be cleaned up.")
#	else:
#		os.system("rm -rf %s*" % today)

def main(womtool_jar: str):
	"""Check syntax and run five workflows"""
	syntaxcheck_passed = syntax_check(womtool_jar)
	print("Checking workflows...")
	print("Not checking check_task_outputs, as its inputs are not local...")

	fuzzycheck_passed = run_workflow("fuzzycheck", ["miniwdl", "run", "check_approximately_equals/fuzzycheck_RData.wdl",
		 "testRDatafile=test_data/allele_chr1.RData",
		 "truthRDatafile=test_data/truths/allele_chr1.RData",
		 "testRDataarray=test_data/allele_chr1.RData",
		 "testRDataarray=test_data/allele_chr2.RData",
		 "truthRDataarray=test_data/truths/allele_chr1.RData",
		 "truthRDataarray=test_data/truths/allele_chr2.RData"])

	required_base_passed = run_workflow("outputs_all_required base case", 
		["miniwdl", "run", "check_wf_outputs/outputs_all_required/parent_req.wdl",
		"file1=test_data/allele_chr1.RData",
		"file2=test_data/truths/allele_chr1.RData",
		"file3=test_data/allele_chr1.RData"])

	required_checker_passed = run_workflow("outputs_all_required checker case",
		["miniwdl", "run", "check_wf_outputs/outputs_all_required/template_req.wdl",
		"file1=test_data/NWD176325.005percent.recab.crai",
		"file2=test_data/NWD119836.0005.recab.cram.crai",
		"file3=test_data/NWD119836.0005.recab.crai",
		"singleTruth=test_data/truths/NWD176325.005percent.recab.crai.txt",
		"truthSet=test_data/truths/NWD119836.0005.recab.cram.crai.txt",
		"truthSet=test_data/truths/NWD119836.0005.recab.crai.txt"])

	optionalouts_base_passed = run_workflow("outputs_some_optional base case",
		["miniwdl", "run", "check_wf_outputs/outputs_some_optional/parent_opt.wdl",
		"optionalInput=test_data/NWD119836.0005.recab.cram.crai",
		"requiredInput=test_data/NWD176325.005percent.recab.crai"])

	optionalouts_checker_passed = run_workflow("outputs_some_optional checker case",
		["miniwdl", "run", "check_wf_outputs/outputs_some_optional/template_opt.wdl",
		"optionalInput=test_data/NWD119836.0005.recab.cram.crai",
		"requiredInput=test_data/NWD176325.005percent.recab.crai",
		"singleTruth=test_data/truths/foo.txt",
		"arrayTruth=test_data/truths/bar.txt",
		"arrayTruth=test_data/truths/second_bar/bar.txt",
		"arrayTruth=test_data/truths/foo.txt"])

	if set([syntaxcheck_passed, fuzzycheck_passed, required_base_passed, required_checker_passed, 
		optionalouts_base_passed, optionalouts_checker_passed]) != set([True]):
		print("At least one workflow failed syntax checking or while running, see above")
		sys.exit(1)

	#cleanup_miniwdl_extras()

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
		assert os.path.isfile(womtool_path), f"User specified womtool is {womtool_path} but there is no file there!"
		main(womtool_path)
