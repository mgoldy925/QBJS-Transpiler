# import sys
import argparse
import re
# from copy import deepcopy
# import os
variables = []

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("qbfile", type=str, help="QB64 file to transpile into JavaScript.")
    parser.add_argument("jsfile", type=str, help="Name of JavaScript with transpiled QB64 code.")
    args = parser.parse_args()

    qb_file = args.qbfile
    js_file = args.jsfile
    transpile(qb_file, js_file)

    print("Success")


def transpile(qb_file, js_file):
    block_patterns = (
        "(FOR)(.*)", "(IF)(.*)(THEN)", "(ELSEIF)(.*)(THEN)", "(ELSE)(.*)", "(WHILE)(.*)", "(SUB)(.*)", "(FUNCTION)(.*)"
    )

    keywords = {
        "WINDOW": windowF,
        "PRINT": printF,
        "LOCATE": locateF,
        "INPUT": inputF,
        "PSET": psetF,
        "CIRCLE": circleF,
        "LINE": lineF,
        "DIM": dimF,
        "COLOR": colorF
    }

    illegal = ("DEFDBL", "AS INTEGER", "AS STRING", "SHARED")

    inside_function = False
    function_name = ""
    inside_block = 0

    with open(qb_file, "r") as qb, open(js_file, "w") as js:
        js.write("import { set_window, print, input, locate, inkeys, color, cls, dim, pset, circle, line, screen, ucase, mid, len } from './graphics.js'\n")
        js.write("function playQB64() {\n")
        for line in qb:
            # If empty line just write it and continue
            if line == "\n":
                js.write(line)
                continue

            # Split line into indentation, code, and comment
            # code = line.lstrip()
            # indentation = line[:line.find(code)]
            (indentation, code) = re.search("(\s*)(.*)", line).groups()
            
            quotes = 0
            for i, ch in enumerate(code):
                quotes += 1 if ch == "\"" else 0
                if (ch == "'" or code[i:i+3] == "REM") and quotes % 2 == 0:
                    length = 1 if ch == "'" else 3
                    new_comment = "//" + code[i+length:]
                    code = code[:i]
                    break
            else:
                new_comment = ""
            
            # matches = re.finditer("\".*?\"", code)
            # last_match = None
            # for last_match in matches:
            #     continue
            # tmp = code
            # if last_match:
            #     tmp = code[last_match.end():]
            # comment = re.search("('|REM).*", code)  # Assuming not ' or REM in a string in the line
            
            # # If there's a comment at the end, remove it from the code
            # new_comment = ""
            # if comment:
            #     code = code[:comment.start()]
            #     new_comment = "//" + comment.group()[comment.end(1)-comment.start(1):]

            # Handle labels, turn them into subroutines, note that indentation will be off inside these
            calling_sub = re.match(r"([\w%!&$#]+):\s*", code)
            if calling_sub and calling_sub.group().strip() == code:
                    code = f"SUB {calling_sub.group(1).strip()}"

            # ':' command can allow for multiple statements on one line
            lines = []
            if ":" in code:
                for index in [m.start() for m in re.finditer(":", line)]:
                    if line.count("\"", 0, index) % 2 == 0:
                        lines.append(code[:index])
                        code = code[index+1:]
            if not lines:
                lines = [code]


            for index, line in enumerate(lines):
                code = line
                # Transpile code

                semicolon = True
                for word in illegal:
                    code = re.sub(f"\\s*{word}\\s*", " ", code)
                
                # Prob don't need this boolean
                if inside_function and function_name in code:
                    code = re.sub(f"{function_name}\s*=", "return", code)

                # Handle gosub, subroutine referenced cannot take args
                for annoying_keyword in ["GOSUB", "GOTO"]:
                    if annoying_keyword in code:
                        code = code[code.find(annoying_keyword)+len(annoying_keyword):].strip() + "()"
                        break
                else:
                    # Check if corresponds to block of code
                    for pattern in block_patterns:
                        # NOTE: re.match() matches w/ beginning of string, use re.search() for anywhere in string
                        match = re.match(pattern, code)
                        if match:
                            code = match.re.sub(blockRepl, code)
                            # print(code)
                            if "function" in code:
                                inside_function = True
                                print(code)
                                function_name = re.search(r"function (.*?\()[^\(]*?", code).group(1)[:-1].strip()
                                print(function_name)
                            # code = statementRepl(code)
                            inside_block += 0 if "else" in code else 1
                            semicolon = False
                            break
                    else:
                        # Check if keyword i.e. PRINT, LOCATE, etc.
                        # These will create extra code to add, so dealing w/ indentation and \n will be annoying
                        # along with when to apply function replacements and such
                        for keyword, func in keywords.items():
                            if keyword in code:
                                #code = statementRepl(code[len(keyword):].strip(), allow_array=keyword!="DIM")
                                code = func(code[code.find(keyword)+len(keyword):].strip())
                                break
                        else:
                            # NOTE: 'END' vs 'END IF' or 'END FUNCTION' is dif here
                            if any([word in code for word in ["END", "NEXT", "WEND", "RETURN"]]):
                                inside_function = any([word in code for word in ["FUNCTION", "SUB"]])
                                if "RETURN" in code and inside_block > 1:
                                    code = "return;"
                                else:
                                    code = "}"
                                    inside_block -= 1
                                semicolon = False

                            code = statementRepl(code, allow_assignment=True)

                if code and new_comment:
                    new_comment = " " + new_comment
                
                if re.search("\s*", code).group() != code and semicolon:
                    code += ";"

                new_code = f"{indentation}{code}"
                new_code += new_comment if index == 0 else ""
                new_code += "" if new_code and new_code[::-1][0] == "\n" else "\n"

                js.write(new_code)
        
        vars = ""
        for variable in variables:
            vars += f"var {variable};\n"
        js.write(vars)
        js.write("}\nexport { playQB64 }")



# Works for if, while, for, function/sub
def blockRepl(match):
    inside = match.group(2).strip()

    # Inside of for loop
    for_match = re.search("(.*)TO(.*)", inside)
    if for_match:
        initialize = for_match.group(1).strip()
        var_name = initialize.split()[0]
        end = for_match.group(2).strip()
        step = "1"

        step_match = re.search("(.*)STEP(.*)", end)
        if step_match:
            end = step_match.group(1).strip()
            step = step_match.group(2).strip()

        inside = f"var {initialize}; {var_name} <= {end}; {var_name} += {step}"

    keyword = match.group(1).lower()
    if keyword == "sub":
        keyword = "function"
    elif keyword == "elseif":
        keyword = "} else if"
    elif keyword == "else":
        keyword = "} else"

    inside = statementRepl(inside, allow_assignment="for"==keyword, allow_array="function"!=keyword)
    if "function" in inside:
        inside += " ()" if "(" not in inside else ""
        inside = "".join(re.split(r"\s+", inside, maxsplit=1))    
    else:
        inside = "" if keyword == "} else" else f"{inside}" if keyword == "function" else f"({inside})"
    
    return f"{keyword} {inside} {{"



# Replace array access, equals, functions, operators
# NOTE: Variables is created when function is created and never changes
def statementRepl(code, allow_assignment=False, allow_array=True): #, variables=[]): temp change
    mappings = (
        {
            "ABS": "Math.abs",
            "SGN": "Math.sign",
            "COS": "Math.cos",
            "SIN": "Math.sin",
            "RND": "Math.random",
            "SQR": "Math.sqrt",
            "CHR$": "String.fromCharCode",
            "TIMER": "",
            "RANDOMIZE": "",
            "_FULLSCREEN": "",
            "INKEY$": "inkeys()",
            "UCASE$": "ucase",
            "MID$": "mid",
            "LEN": "len",
            "CLS": "cls()",
            "SCREEN 12": "screen(12)"  # THIS WORKS FOR NOW
        },

        {
            "AND": "&&",
            "OR": "||",
            "NOT": "!",
            "<>": "!=",
            "MOD": "%",
            "^": "**"
        }
    )
    
    new_code = code

    # Replace array notation
    if allow_array:
        new_code = re.sub(r"([\w%!&$#]+?)\s*\((.*?)\)", lambda match : f"{match.group(1)}[" + re.sub(r',\s*', '][', match.group(2)) + "]" if match.group(1) not in list(mappings[0].keys()) + list(mappings[1].keys()) else match.group(), code)

    # Replace function calls and operators
    for mapping in mappings:
        pattern = "|".join([re.escape(key) if "$" in key else key for key in mapping])
        new_code = re.sub(pattern, lambda match : mapping[match.group()] if match.group() else "", new_code)

    # Change assignments
    # Replaces all '=' with '==' except first occurence
    if allow_assignment:
        n = re.subn(r"\s+=\s+", " == ", new_code)[1]
        new_code = re.sub(r"\s+=\s+", " == ", new_code[::-1], n)[::-1] if n > 1 else new_code
        # new_code = "var " + new_code
    else:
        new_code = re.sub(r"\s+=\s+", " == ", new_code)
    # - 1 if allow_assignment else 0
    # new_code = re.sub(r"\s+=\s+", " == ", new_code[::-1], n)[::-1]
    # new_code = new_code[::-1]

    assignment = re.match(r"([\w%!&$#]+?)\s+=\s+", new_code)
    if assignment:
        name = assignment.group(1).strip()  # Already stripped, but just in case
        if name not in variables:
            # new_code = "var " + new_code
            variables.append(name)

    return new_code





# NOTE: Remember to split :'s earleir in code
# Gotta add PRINT USING
# This is rlly inefficient, def a way better way w/ regex
# First split literal strings, then split ;'s and ,'s
def printF(code):
    chars = list(code[::-1])
    
    expressions = []
    while chars:
        arg = ""
        ch = chars.pop()
        if ch == "\"":
            arg += "'"
            ch = chars.pop()
            while chars and ch != "\"":
                arg += ch
                ch = chars.pop()
            arg += "'"
        elif ch in [";", ",", "+"]:
            arg = f"'{ch}'"
        elif ch == " ":
            continue
        else:
            arg += ch
            while chars and ch not in [" ", ";", ",", "+"]:
                ch = chars.pop()
                arg += ch
            if ch in [";", ",", "+"]:
                expressions.append(statementRepl(arg[:-1]))  # Hack
                arg = f"'{ch}'"
        if arg:
            expressions.append(statementRepl(arg))
    
    return f"print({', '.join(expressions)})"


def windowF(code):
    args = [statementRepl(arg.strip()) for arg in re.search(r"\((.*),(.*)\)-\((.*),(.*)\)", code).groups()]
    return f"set_window({', '.join(args)})"


def inputF(code):
    match = re.search("(.*)\"(.*)\"(.*)", code)
    same_line = "true" if code[0] == ";" else "false"
    if match:
        args = [arg.strip() for arg in match.groups()]
        question_mark = "true" if args[2][0] == ";" else "false"
        prompt = f"'{args[1]}'"
        vars = re.split(r",\s*", args[2][1:].strip())
    else:
        index = 1 if same_line else 0
        question_mark = "true"
        prompt = "''"
        vars = [statementRepl(var) for var in re.split(r",\s*", code[index:].strip())]
    return f"[{', '.join(vars)}] = input({same_line}, {question_mark}, {prompt}, {len(vars)})"


def locateF(code):
    args = [statementRepl(arg.strip()) for arg in re.search(r"(.*)(,.*)", code).groups()]
    args[1] = "null" if not args[1] else args[1][1:].strip()
    return f"locate({', '.join(args)})"


def dimF(code):
    args = [(arg[0].strip(), arg[1].strip()) for arg in re.findall(r"([\w%!&$#]+)\((.*?)\)", code)]
    new_code = "var "
    new_args = []
    for arg in args:
        (name, size) = arg # re.search(r"([\w%!&$#]+)\((.*)\)", arg).groups()
        new_args.append(f"{name} = dim({size})")
    return new_code + ", ".join(new_args)


def psetF(code):
    args = [statementRepl(arg.strip()) for arg in re.search(r"\((.*),(.*)\)(.*)", code).groups()]
    args[2] = args[2][1:].strip() if args[2] else "null"
    return f"pset({', '.join(args)})"


def circleF(code):
    args = [statementRepl(arg.strip()) for arg in re.search(r"\((.*),(.*)\),\s*([^,]*)(.*)", code).groups()]
    args[3] = args[3][1:].strip() if args[3] else "null"
    return f"circle({', '.join(args)})"


def lineF(code):
    try:
        args = [statementRepl(arg.strip()) for arg in re.search(r"\((.*),(.*)\)-\((.*),(.*)\)(.*)", code).groups()]
    except AttributeError:
        args = [statementRepl(arg.strip()) for arg in re.search(r"-\((.*),(.*)\)(.*)", code).groups()]
    num_points = len(args)-1
    optional_args = [optional_arg.strip() for optional_arg in args[num_points][1:].strip().split(",")]
    args[num_points] = "null"
    args.append("null")
    if "" not in optional_args:
        for arg in optional_args:
            # Assuming args must be a color number and/or a B/BF
            if "B" in arg:
                args[num_points+1] = arg
            else:
                args[num_points] = arg if arg else "null"
    args = [f"[{', '.join([args[i] for i in range(num_points)])}]", args[num_points], args[num_points+1]]
    return f"line({', '.join(args)})"


def colorF(code):
    return f"color({map_color[code.strip()]})"


def map_color(color):
    colors = {
        "0": "rgb(0, 0, 0)",
        "1": "rgb(0, 0, 170)",
        "2": "rgb(0, 170, 0)",
        "3": "rgb(0, 170, 170)",
        "4": "rgb(170, 0, 0)",
        "5": "rgb(170, 0, 170)",
        "6": "rgb(170, 85, 0)",
        "7": "rgb(170, 170, 170)",
        "8": "rgb(85, 85, 85)",
        "9": "rgb(85, 85, 255)",
        "10": "rgb(85, 255, 85)",
        "11": "rgb(85, 255, 255)",
        "12": "rgb(255, 85, 85)",
        "13": "rgb(255, 85, 255)",
        "14": "rgb(255, 255, 85)",
        "15": "rgb(255, 255, 255)"
    }
    return colors[color] if color else "null"

if __name__ == "__main__":
    main()