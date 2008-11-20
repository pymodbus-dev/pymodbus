#!/bin/bash
#---------------------------------------------------------------------------# 
# Global Variables
#---------------------------------------------------------------------------# 
root="../../"
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
do_doctest()
{
	# Remove all old reports as we append
	[ -f doctest.report ] && rm doctest.report

	# Check for and run small doctest and only report errors
	for file in $files; do
		python $file >> doctest.report
	done
}

#---------------------------------------------------------------------------# 
# Run doctest with verbose setting on (produces larger report)
#---------------------------------------------------------------------------# 
do_doctest_full()
{
	# Remove all old reports as we append
	[ -f doctest.report ] && rm doctest.report

	# Check for and run pyflakes for each python file
	for file in $files; do
		header doctest.report "${file##*/} Results"
		python $file -v >> doctest.report
	done
}

#---------------------------------------------------------------------------# 
# Print the script help message
#---------------------------------------------------------------------------# 
do_help()
{
	cat <<EOF
$0 <one of below>
	r,run	- Run the doctest for all files
	f,full	- Run the verbose doctest for all files
	c,clean	- Remove any created files from the tests
	h,help	- This message
EOF
}

#---------------------------------------------------------------------------# 
# Main
# @param $1 The command to execute
#---------------------------------------------------------------------------# 
case "$@" in
	r|"run")
		do_doctest
	;;

	f|"full")
		do_doctest_full
	;;

	c|"clean")
		[ -f doctest.report ] && rm doctest.report
	;;

	*)
		do_help
	;;
esac
