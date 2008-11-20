#!/usr/bin/env python
'''
Script to automatically generate PyTable documentation
'''
import pydoc2

if __name__ == "__main__":
	excludes = [
		"Numeric",
		"_tkinter",
		"Tkinter",
		"math",
		"string",
		"twisted",
	]
	stops = [
	]

	modules = [
		'pymodbus',
		'__builtin__',
	]	
	pydoc2.PackageDocumentationGenerator(
		baseModules = modules,
		destinationDirectory = ".",
		exclusions = excludes,
		recursionStops = stops,
	).process ()
	
