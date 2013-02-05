# Main package: execute commandline when calling `python -m nxdd`

if __name__ == "__main__":
	import sys
	from nxdd.commandline import main
	return main(sys.argv)