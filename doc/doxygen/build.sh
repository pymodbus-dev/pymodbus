#!/bin/bash

#---------------------------------------------------------------------------# 
# Builds the doxygen documentation
#---------------------------------------------------------------------------# 
do_build()
{
	if [ -f "`which doxygen`" ]; then
		doxygen .doxygen
	else
		echo "Doxygen not installed, failing"
	fi
}

#---------------------------------------------------------------------------# 
# Cleans any files created from build
#---------------------------------------------------------------------------# 
do_clean()
{
	rm -rf html doxygen.warnings > /dev/null 2>&1
}


#---------------------------------------------------------------------------# 
# Print the script help message
#---------------------------------------------------------------------------# 
do_help()
{
	cat <<EOF
$0 <one of below>
	b,build	- Builds the doxygen documentation
	c,clean	- Remove any created files from build
	h,help	- This message
EOF
}

#---------------------------------------------------------------------------# 
# Main
# @param $1 The command to execute
#---------------------------------------------------------------------------# 
case "$@" in
	b|"build")
		do_build
	;;

	c|"clean")
		do_clean
	;;

	*)
		do_help
	;;
esac
