#!/bin/bash
#---------------------------------------------------------------------------# 
# Global Variables
#---------------------------------------------------------------------------# 
root="../../"
files=`find $root | grep "py$"`

#---------------------------------------------------------------------------# 
# @brief Build a section header
# @param $1 The file to output to
# @param $2 The header to append to the section
#---------------------------------------------------------------------------# 
header()
{
	echo "#---------------------------------------------------------------------------#" >>$1
	echo "# $2"                                                                          >>$1
	echo "#---------------------------------------------------------------------------#" >>$1
}

#---------------------------------------------------------------------------# 
# Run all the available lint commands on the source tree
#---------------------------------------------------------------------------# 
do_lint()
{
	# Remove all old reports as we append
	rm *.report

	# Check for and run pyflakes for each python file
	if [ "`which pyflakes`" != "" ]; then
		OPTS=""
		RUN="`which pyflakes` $OPTS"
		for file in $files; do
			header ${file##*/}.report "PyFlakes Report"
			$RUN $file >> ${file##*/}.report 2>&1
		done
	fi

	# Check for and run pychecker for each python file
	if [ "`which pychecker`" != "" ]; then
		OPTS="--config=.pychecker"
		RUN="`which pychecker` $OPTS"
		for file in $files; do
			header ${file##*/}.report "PyChecker Report"
			$RUN $file >> ${file##*/}.report 2>/dev/null
		done
	fi

	# Check for and run pyflakes for each python file
	if [ "`which pylint`" != "" ]; then
		OPTS="--rcfile=.pylint"
		RUN="`which pylint` $OPTS"
		for file in $files; do
			header ${file##*/}.report "PyLint Report"
			$RUN $file >> ${file##*/}.report 2>/dev/null
		done
	fi
}

#---------------------------------------------------------------------------# 
# Print an excerpt from the reports with the final pylint scores
#---------------------------------------------------------------------------# 
do_tally()
{
	msg="Your code has been rated"
	ls *.report > /dev/null 2>&1
	if [ "$?" == "0" ]; then
		grep "$msg" *.report | awk {' print $1" score is " $7 '}
	else
		echo "There are no available reports, please run lint first"
	fi
}

#---------------------------------------------------------------------------# 
# Print the script help message
#---------------------------------------------------------------------------# 
do_help()
{
	cat <<EOF
$0 (lint|tally|help)
	lint	- Run all available lint commands on the source tree
	tally	- Return the final pylint scores from all the reports
	help	- This message
EOF
}

#---------------------------------------------------------------------------# 
# Main
# @param $1 The command to execute
#---------------------------------------------------------------------------# 
case "$@" in
	"lint")
		do_lint
	;;

	"tally")
		do_tally
	;;

	*)
		do_help
	;;
esac
