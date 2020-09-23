import sys


if __name__ == "__main__":
    graphStarted = False
    validStarts = {"val:": 1, "owf:": 2, "chi:": 3, "par:": 4}
    prevLine = ""
    outLine = ""
    infile = sys.argv[1]
    outfile = sys.argv[1] + ".cleaned"
    
    with open(infile, "r") as inf:
        with open(outfile, "w") as outf:
            for line in inf:
                if graphStarted:
                    if line[0:4] in validStarts:
                        #if outLine != "":
                        outf.write(outLine + "\n")
                        outLine = line.strip()
                    else:
                        outLine += " " + line.strip()
                elif "Scale graph nodes:" in line:
                    graphStarted = True
                    outf.write(line)
                else:
                    outf.write(line)
                
                prevLine = line
            outf.write(outLine + "\n")
