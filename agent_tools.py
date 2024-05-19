from os.path import exists

def replacelineswith(filename, linestart, lineend, newcontent):
    """Replaces lines in a file with new content.

    Args:
        filename: The path to the file.
        linestart: The starting line number (inclusive).
        lineend: The ending line number (inclusive).
        newcontent: The new content to replace the lines.
    """
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
        if 1 <= linestart <= len(lines) and 1 <= lineend <= len(lines) and linestart <= lineend:
            lines[linestart - 1:lineend] = [newcontent + '\n']
            with open(filename, 'w') as file:
                file.writelines(lines)
            print(f"Lines {linestart} to {lineend} in '{filename}' replaced with '{newcontent}'.")
        else:
            print(f"Invalid line numbers: linestart={linestart}, lineend={lineend}.")
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def insertafterline(filename, linebefore, content):
    """Inserts content after a specified line in a file.

    Args:
        filename: The path to the file.
        linebefore: The line number to insert after (inclusive).
        content: The content to insert.
    """
    print('content', repr(content))
    print('replacing doublebackslash-n with backslash-n')
    content = content.replace('\\n', '\n')
    print('now content is', repr(content))
    try:
        with open(filename, 'r') as file:
            lines = file.readlines()
        if 0 <= linebefore <= len(lines):
            lines.insert(linebefore, '\n' + content + '\n')
            with open(filename, 'w') as file:
                file.writelines(lines)
            print(f"Content '{content}' inserted after line {linebefore} in '{filename}'.")
        else:
            print(f"Invalid line number: linebefore={linebefore}")
    except FileNotFoundError:
        print(f"File '{filename}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

def tool_insertafterline(input_dict):
    print('Insertafterline TOOL', input_dict)
    assert 'filename' in input_dict, 'filename is required'
    assert 'linebefore' in input_dict, 'linebefore is required'
    assert 'content' in input_dict, 'content is required'
    assert input_dict['linebefore'].isdigit(), 'linebefore must be a string which is a digit'
    assert exists(input_dict['filename']), 'file does not exist'
    return insertafterline(input_dict['filename'], int(input_dict['linebefore']), input_dict['content'])

def singlelineedit(filename, lineNumber, newLineContent):
    with open(filename, 'r') as file:
        lines = file.readlines()

    if lineNumber < len(lines) + 1 and lineNumber >= 1:
        lines[lineNumber-1] = newLineContent + '\n'

        with open(filename, 'w') as file:
            for line in lines:
                file.write(line)

        return "Line {} in {} has been edited.".format(lineNumber, filename)
    else:
        return "Line number {} is out of range for file {}.".format(lineNumber, filename)

def tool_settimer(input_dict):
    print('SETTIMER TOOL', input_dict)

def tool_editsingleline(input_dict):
    print('EDITSINGLELINE TOOL', input_dict)
    assert 'filename' in input_dict, 'filename is required'
    assert 'linenumber' in input_dict, 'linenumber is required'
    assert 'newlinecontent' in input_dict, 'newlinecontent is required'
    assert input_dict['linenumber'].isdigit(), 'linenumber must be a string which is a digit'
    assert exists(input_dict['filename']), 'file does not exist'
    return singlelineedit(input_dict['filename'], int(input_dict['linenumber']), input_dict['newlinecontent'])

def tool_replacelineswith(input_dict):
    print('EDITSINGLELINE TOOL', input_dict)
    assert 'filename' in input_dict, 'filename is required'
    assert 'startline' in input_dict, 'linenumber is required'
    assert 'newcontent' in input_dict, 'newcontent is required'
    assert input_dict['startline'].isdigit(), 'linenumber must be a string which is a digit'
    assert input_dict['endline'].isdigit(), 'linenumber must be a string which is a digit'
    assert exists(input_dict['filename']), 'file does not exist'
    return replacelineswith(input_dict['filename'], 
                          int(input_dict['startline']),
                          int(input_dict['endline']),
                          input_dict['newcontent'])


tools_functions_map = {
    'settimer': tool_settimer,
    'editsingleline': tool_editsingleline,
    'insertafterline': tool_insertafterline,
    'replacelineswith': tool_replacelineswith
}