import re
from parse import *
from opcodes import *
                
def parse_opcode_line(opcode_line):
    line = opcode_line.split('  ')
    line = [x.replace('*', '').replace('>', '').replace('\n', '').replace('\'', '').strip() for x in line]
    line = [x for x in line if x != 'E' and x != 'global']
    line_items = []

    for l in line:
        if l != '':
            line_items.append(l)
    
    if len(line_items) < 2:
        print("parse_opcode_line: Error, unexpected number of items in a line.")
        print("line:", opcode_line)
    else:# if len(line_items) >= 2         
        if line_items[1].isdigit(): # оставляем лишь линейные индексы (ветки и циклы игнорируем)
            line_items.pop(0)
    
    if len(line_items) > 2 and line_items[2].isdigit():
         line_items.pop(2) # избавляемся от значений из колонки ext
         
    if len(line_items) not in [2,3,4]: # должны остаться значения из колонок индекс, опкод, возвращаемое значение и операнды
        print("parse_opcode_line: Error, unexpected number of items in a line.")
        print("line:", opcode_line)
        
    opcode = Opcode()
    opcode.index = line_items[0]
    opcode.operation = line_items[1]
    if len(line_items) == 3: # определяем какой колонке принадлежит 3-й элемент - возвращаемое значение или операнд
        if line_items[2] == line[-1]:
            opcode.operands = line_items[2].split(', ')
        else:
            opcode.ret_value = line_items[2]
    elif len(line_items) == 4:
        opcode.ret_value = line_items[2]
        opcode.operands = line_items[3].split(', ') 
    
    return opcode
    
def parse_file(filename):
    EntryPoints = []
    opcode_line_pattern = r"[\d]{1,10}\*{0,1} * [\d]{0,10} * E{0,1} >{0,1} >{0,1} * ([A-Z]{1,32}_{0,1}){0,10} *"
    
    file = open(filename, "r")
    ep_count = 0
    while True:
        line = file.readline()
        if not line:
            break
        if "Finding entry points" in line: 
            ep_count += 1
            EP = EntryPoint()
            done = 0
            while True:
                line = file.readline()
                if not line:
                    break
                if done == 1:
                    break
                if "filename:       " in line:
                    #filename:       qwerty
                    filename = parse("filename:       {value}", line)
                    EP.filename = filename['value']
                    
                    #function name:  ytrewq
                    line = file.readline()
                    if not line:
                        break
                    func = parse("function name:  {value}", line)
                    EP.function_name = func['value']
                    
                    #number of ops:  12345
                    line = file.readline()
                    if not line:
                        break
                    ops_num = parse("number of ops:  {value}", line)
                    EP.number_of_ops = ops_num['value']
                    
                    #compiled vars:  !0 = $qwer123, !1 = $321rewq, !2 = $asdfg
                    line = file.readline()
                    if not line:
                        break
                    vars_str = parse("compiled vars:  {value}", line)
                    EP.set_compiled_vars(vars_str['value'])
                    
                    #line #* E I O op fetch ext return operands                    
                    line = file.readline()
                    if not line:
                        break
                        
                    #-------------------------------------------
                    line = file.readline()
                    if not line:
                        break
                     
                    for i in range(0, int(ops_num['value'])):
                        #123 321 E > QWER_TY 
                        line = file.readline()
                        if re.search(opcode_line_pattern, line):
                            op = parse_opcode_line(line)
                            EP.opcodes.append(op)
                        else: 
                            if not re.match(r'^\s*$', line):
                                print("parse_file: Error, unexpected line.")
                                print("line:", line)
                                break           
                        
                    EntryPoints.append(EP)
                    done = 1             
    file.close
    
    return EntryPoints

#Если не дождаться завершения всех вызовов функций, в опкоды может быть записана обрывающаяся точка входа (строк опкодов меньше, чем заявлено), кроме того следующая точка входа начинается без переноса строки, что приводит к ошибкам парсинга.
#Данная функция добавляет переносы строки для всех вхождений "Finding entry points" и записывает все в новый файл.
def parse_error_correction(old_file):
    #old_file = open(filename, "r")
    new_filename = "../Logs/opcodes.txt"
    new_file = open(new_filename, "a")
    new_file.truncate(0)
    while True:
        line = old_file.readline()
        if not line:
            break
        if "Finding entry points" in line: 
            correct_part = line.replace("Finding entry points", "")
            if correct_part:
                new_file.write(correct_part)              
                new_file.write("\nFinding entry points\n") 
        else:
            new_file.write(line)                     
    #old_file.close  
    new_file.close

#Печать в лог информации о всех точках входа в исследуемом файле.
#На вход подается массив точек входа после исполнения функции parse_file.
def print_entry_points(EntryPoints):
    ep_filename = "../Logs/entry_points.txt"
    ep_file = open(ep_filename, "a")
    ep_file.truncate(0)
    for eps in EntryPoints:
        ep_file.write("-----------------------------------------------\n")
        ep_file.write("Entry point №{}\n".format(EntryPoints.index(eps)+1))
        ep_file.write("Filename: {}\n".format(eps.filename))
        ep_file.write("Function name: {}\n".format(eps.function_name))
        ep_file.write("Number of opcodes: {}\n".format(eps.number_of_ops))
        ep_file.write("Compiled variables:\n")
        ep_file.write("---------------------\n")
        for cv in eps.compiled_variables:
            ep_file.write("{}\t{}\n".format(cv.ID, cv.name))
        ep_file.write("---------------------\n")
        ep_file.write("Opcodes:\n")
        ep_file.write("---------------------\n")
        for o in eps.opcodes:
            ep_file.write("{}\t{} \t{}\t{}\n".format(o.index, o.operation, o.ret_value, ', '.join(o.operands)))
        ep_file.write("---------------------")
    ep_file.close()
        
def get_statements_from_opcodes(opcodes):
    Statements = []
    index = 1
    STMT = Statement()
    for o in opcodes:
        if o.operation == "EXT_STMT":
            Statements.append(STMT)
            STMT = Statement()
            STMT.index = index
            index += 1
        STMT.opcodes.append(o)       
    Statements.append(STMT)
    Statements.pop(0)
    return Statements

def print_statements(Statements):
    stmt_filename = "../Logs/statements.txt"
    stmt_file = open(stmt_filename, "a")
    stmt_file.truncate(0)
    for s in Statements:
        stmt_file.write("Statement №{} \n".format(s.index))
        for o in s.opcodes:
            stmt_file.write("{}\t{} \t{}\t{}\n".format(o.index, o.operation, o.ret_value, ', '.join(o.operands)))
        stmt_file.write("----------------------------------------------------\n")
    stmt_file.close()
    
