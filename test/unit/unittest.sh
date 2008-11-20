#!/bin/bash
#---------------------------------------------------------------------------# 
# Global Variables
#---------------------------------------------------------------------------# 
root="."
files=`find $root | grep "py$"`

#---------------------------------------------------------------------------# 
# Build a section header
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
# Run doctest and only report errors
#---------------------------------------------------------------------------# 
do_unittest()
{
	# Remove all old reports as we append
	[ -f unittest.report ] && rm unittest.report

	# Check for and run small doctest and only report errors
	for file in $files; do
		python $file >> unittest.report 2>&1
	done
}

#---------------------------------------------------------------------------# 
# Run doctest with verbose setting on (produces larger report)
#---------------------------------------------------------------------------# 
do_unittest_full()
{
	# Remove all old reports as we append
	[ -f unittest.report ] && rm unittest.report

	# Check for and run pyflakes for each python file
	for file in $files; do
		header unittest.report "${file##*/} Results"
		python $file -v >> unittest.report 2>&1
		echo -e "\n" >> unittest.report
	done
}

#---------------------------------------------------------------------------# 
# Print the script help message
#---------------------------------------------------------------------------# 
do_help()
{
	cat <<EOF
$0 <one of below>
	r,run	- Run the unittest for all files
	f,full	- Run the verbose unittest for all files
	c,clean	- Removes any created files from the test
	h,help	- This message
EOF
}

#---------------------------------------------------------------------------# 
# Main
# @param $1 The command to execute
#---------------------------------------------------------------------------# 
case "$@" in
	r|"run")
		do_unittest
	;;

	f|"full")
		do_unittest_full
	;;

	c|"clean")
		[ -f unittest.report ] && rm unittest.report
		rm *.pyc > /dev/null 2>&1
	;;

	*)
		do_help
	;;
esac
