import sys
import os
import re
import opcodes_parser as op
import opcodes_analyzer as oa          
import vulns


if __name__ == '__main__':

    args = sys.argv[1:] # python3 main.py -scan_mode mode -opcode_file filename -scan_dir dirname

    if len(args)== 4 and args[0] == '-scan_mode':
        if args[1] == "rxss":
            scan_mode = vulns.RXSS
        elif args[1] == "sqli":
            scan_mode = vulns.SQLI
        else:
            print("\nThe scan_mode is specified incorrectly.\n")
            sys.exit()
            
        if args[2] == '-opcode_file':
            if os.path.isfile(args[3]):
                opcode_file = open(args[3], "r")
            else:
                print("\nThe opcode_file is specified incorrectly.\n")
                sys.exit()
            
        if args[2] == '-scan_dir':
            if os.path.isdir(args[3]):
                scan_dir = args[3]
            else:
                print("\nThe scan_dir is specified incorrectly.\n")
                sys.exit()
                
            with open('../VLD_0.17.1_modified_version/vld.c', 'r') as file :
                filedata = file.read()
            pattern = ""
            filedata = re.sub(r"char ScanDir\[\] = .*", "char ScanDir[] = " + "\"" + scan_dir + "\";", filedata)
            with open('../VLD_0.17.1_modified_version/vld.c', 'w') as file:
                file.write(filedata)
                
            os.system("sh ../Scripts/STOP_VLD.SH")
            os.system("sh ../Scripts/REBUILD_VLD.SH")
            os.system("sh ../Scripts/START_VLD.SH") 
            
            print("\nTo stop VLD and analyze the received opcodes, press \"s\"...\n")
            input_symbol = input()
            if(input_symbol == 's'):
            	os.system("sh ../Scripts/STOP_VLD.SH")
            	if os.path.isfile("/var/www/html/vld_output.txt"):
            	    opcode_file = open("/var/www/html/vld_output.txt", "r")
            	else:
                    print("\nThe opcode_file is specified incorrectly.\n")
                    sys.exit()
            else:
            	print("\nError: unexpected input\n")
            	os.system("sh ../Scripts/STOP_VLD.SH")
            	sys.exit()
                    
        print("\n Start of opcode analysis \n")
        op.parse_error_correction(opcode_file)
        EPs = op.parse_file("../Logs/opcodes.txt")
        op.print_entry_points(EPs)
        for ep in EPs:
           Statements = op.get_statements_from_opcodes(ep.opcodes)
           op.print_statements(Statements)
           oa.analyze(ep, scan_mode)
        opcode_file.close() 
        
        print("\n End of opcode analysis \n")
                                   
    else:
        print("\nThe scan_mode or opcode_file for analysis is not specified \nor is there an error in the passed arguments.\n")


    

