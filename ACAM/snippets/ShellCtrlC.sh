#!/bin/sh

#
# a snippet to test catching "Ctrl+C"
#


for j in 1 2 3 4
	do			
		
		trap 'echo "  ***Ctrl+C caught, exiting!***"; echo "abort ACAM"; exit 0' SIGINT
		echo "$j"
		sleep 15
		echo "testing github"

	done

