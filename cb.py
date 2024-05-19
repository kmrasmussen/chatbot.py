#!/usr/bin/env python3
import readline
import os
from os.path import exists, join
from colorama import Fore, Style
from codeblocks import add_code_copy_tag_to_response_text
import pyperclip
from uuid import uuid4
import pickle
import sys

from config import *
from state import *
from agentshell import AgentShell
from completion import get_completion
from utils import *
from agent_tools import tools_functions_map

TOOLDESCRIPTION_PROMPT =  open(TOOLS_PROMPT_FILENAME, 'r').read()
print('tool prompt xml', extract_actions_dicts(TOOLDESCRIPTION_PROMPT))

# These lines are for smart navigation using option + arrow keys
readline.parse_and_bind('tab: complete')
histfile = '.my_clihistory'
try:
    readline.read_history_file(histfile)
except FileNotFoundError:
    pass

if not exists('blocks.txt'):
    with open('blocks.txt', 'w') as f:
        f.write('')

if exists(nodes_pickle_filename):
    with open(nodes_pickle_filename, 'rb') as f:
        nodes = pickle.load(f)
else:
    nodes = Nodes()

if exists(codeblocks_pickle_filename):
    with open(codeblocks_pickle_filename, 'rb') as f:
        codeblocks = pickle.load(f)
else:
    codeblocks = CodeBlocks()

if USE_REDIS_CLIPBOARD:
    import redis
    # Configure Redis connection
    redis_host = 'localhost'  # Replace with your Redis host
    redis_port = 6379       # Replace with your Redis port
    redis_password = os.getenv('REDIS_PASSWORD')
    redis_channel = 'clipboard'

    # Connect to Redis
    r = redis.Redis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)

class StateDict:
    def __init__(self):
        self.dict = {}
        self.multiline = False
        self.model = 'openai/gpt-3.5-turbo'

    def save_as_pickle(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(self, f)

if exists(statedict_pickle_filename):
    with open(statedict_pickle_filename, 'rb') as f:
        statedict = pickle.load(f)
else:
    statedict = StateDict()

def save_nodes():
    nodes.save_as_pickle(nodes_pickle_filename)
def save_codeblocks():
    codeblocks.save_as_pickle(codeblocks_pickle_filename)
def save_codeblocks():
    codeblocks.save_as_pickle(codeblocks_pickle_filename)
def save_statedict():
    statedict.save_as_pickle(statedict_pickle_filename)


# function that adds a string to blocks.txt
def add_block_to_file(block):
    with open('blocks.txt', 'a') as f:
        f.write(block + '\n')

command_list = ['exit', 'cp', 'clear', 'x', 'prefixshow', 'sethead', 'bash', 'bbash', 'lbp', 'ml', 
                'model', 'model?', 'statedict', 'openfile', 'closefile', 'openfiles?'
                ]

def handle_user_input(user_input, last_node_id):
    preprompt = ''
    if USE_TOOLS:
        preprompt = TOOLDESCRIPTION_PROMPT + '\n'
    
    print('user input', user_input)
    openfiles_preprompt = ''
    if 'openfiles' in statedict.dict and len(statedict.dict['openfiles']) > 0:
        openfiles_preprompt += f'open files list: {statedict.dict["openfiles"]}\n'
        for filename in statedict.dict['openfiles']:
            if exists(filename):
                file_lines = open(filename, 'r').readlines()
                file_lines_numbered = ['%d|%s' % (i+1, line) for i, line in enumerate(file_lines)]
                file_content = ''.join(file_lines_numbered) #open(filename, 'r').read()
                openfiles_preprompt += f'current contents  of file {filename} :\n{file_content}\n'
        print(openfiles_preprompt)
    preprompt += openfiles_preprompt

    user_node = nodes.add_node(last_node_id, user_input, 'user')    
    messages = nodes.get_messages()
    #if len(messages) > 0:
    print('first message', messages[0])
    assert messages[0]['role'] == 'user'
    messages[0]['content'] = preprompt + messages[0]['content']
    #else:
    #    user_input = openfiles_preprompt + user_input
    response_text = get_completion(messages, 
                                   statedict.model,
                                   OPENROUTER_API_KEY,
                                   add_assistant_response=False)
    print(user_node.id)
    assitant_node = nodes.add_node(user_node.id, response_text, 'assistant')
    last_node_id = assitant_node.id
    response_text_with_copy_tags, response_code_blocks = add_code_copy_tag_to_response_text(response_text, len(codeblocks.blocks))
    codeblocks.blocks += response_code_blocks
    for block in response_code_blocks:
        add_block_to_file(block)
    print(Fore.WHITE + response_text_with_copy_tags)
    print(assitant_node.id)
    print(Style.RESET_ALL)

    if USE_TOOLS:
        tool_actions = extract_actions_dicts(response_text)
        print('tool actions', tool_actions)
        for tool_action in tool_actions:
            print('tool action', tool_action)
            if tool_action['tool'] in tools_functions_map:
                apply_tool = input('apply tool? do (d), skip (s), skip all (x): ')
                if apply_tool == 's':
                    continue
                elif apply_tool == 'x':
                    break
                else:
                    tool_function = tools_functions_map[tool_action['tool']]
                    tool_output = tool_function(tool_action)
                    print('tool output', tool_output)
            else:
                print('tool not found in tools_functions_map')
    return last_node_id

cwd = os.getcwd()
tw = AgentShell(cwd=cwd)
messages = nodes.get_messages()
last_node_id = nodes.latest_node_id
#print('last id', last_node_id)
last_bash_input, last_bash_output = None, None


def do_round(user_input):
    global last_node_id
    global last_bash_input
    global last_bash_output
    global continue_after_command

    continue_after_command = True
    # check if user input is a command
    if user_input.startswith('@'):
        # command is the first word after ! until space, the argument string is the rest
        command = user_input[1:].split(' ')[0]
        command_arg = user_input[1 + len(command):].strip()
        #print('command', command, 'arg', command_arg)
        if command in command_list:
            if command == 'x' or command == 'exit':
                print('exiting')
                save_nodes()
                return False
            elif command == 'cp':
                # copy the code block to clipboard
                codeblock = codeblocks.blocks[int(command_arg)].strip()
                if USE_REDIS_CLIPBOARD:
                    r.publish('clipboard', codeblock)
                    print('published to clipboard:', codeblock)
                else:
                    pyperclip.copy(codeblock)
                    print(codeblock)
            elif command == 'bbash':
                try:
                    # copy the code block to clipboard
                    #print('bbash', int(command_arg))
                    codeblock = codeblocks.blocks[int(command_arg)].strip()
                    print(Fore.YELLOW + codeblock)
                    #print('agent shell should run this:', codeblock)
                    roundtrip_dict = tw.round_trip(codeblock)
                    command_output = roundtrip_dict['command_output']
                    last_bash_input, last_bash_output = codeblock, command_output
                    #print('command_output:')
                    print(Fore.WHITE + command_output)
                    print(Style.RESET_ALL)
                except Exception as e:
                    print('error in bbash', e)
            elif command == 'bash':
                print(Fore.YELLOW + command_arg)
                #print('agent shell should run this:', codeblock)
                roundtrip_dict = tw.round_trip(command_arg)
                command_output = roundtrip_dict['command_output']
                last_bash_input, last_bash_output = command_arg, command_output
                #print('command_output:')
                print(Fore.WHITE + command_output)
                print(Style.RESET_ALL)
            elif command == 'lbp':
                #print('last bash input:', last_bash_input)
                #print('last bash output:', last_bash_output)
                lbp_xml = '<stdin>' + '\n' + last_bash_input + '\n' + '<stdin>\n<stdout>' + '\n' + last_bash_output + '\n' + '<stdout>' + '\n'
                #print('lbp_xml', lbp_xml)
                last_node_id = handle_user_input(lbp_xml, last_node_id)
            elif command == 'clear':
                messages = []
                nodes.latest_node_id = None
            elif command == 'prefixshow':
                if command_arg.isdigit():
                    codeblock = codeblocks.blocks[int(command_arg)].strip()
                    print(codeblock)
                else:
                    prefix = command_arg
                    node = nodes.prefix2id(prefix)
                    if node:
                        print(Fore.WHITE + node.content)
                        print(Style.RESET_ALL)
                    else:
                        print('node not found or multiple nodes found with prefix')
            elif command == 'sethead':
                prefix = command_arg
                node = nodes.prefix2id(prefix)
                if node:
                    if node.role == 'user':
                        # not allowed
                        print('cannot set head to user node')
                    elif node.role == 'assistant':
                        nodes.latest_node_id = node.id
                        print('set head to', node.id)
                    else:
                        raise Exception('unknown role in sethead')
            elif command == 'ml':
                statedict.multiline = not statedict.multiline
                print('multiline mode:', statedict.multiline)
            elif command == 'model':
                statedict.model = command_arg
                print('openrouter model set to', statedict.model)
                print('cb.py does not check if the model is valid, see list at https://openrouter.ai/models')
            elif command == 'model?':
                print('openrouter model set to', statedict.model)
                print('cb.py does not check if the model is valid, see list at https://openrouter.ai/models')
                print('openai/gpt-4o, openai/gpt-4-turbo, google/gemini-flash-1.5, anthropic/claude-3-haiku, anthropic/claude-3-opus')
            elif command == 'statedict':
                print('statedict:', statedict.__dict__)
            elif command == 'openfile':
                abs_path = os.path.abspath(command_arg)
                print('abs_path', abs_path)
                if not exists(abs_path):
                    print('file does not exist')
                else:
                    if 'openfiles' not in statedict.dict:
                        statedict.dict['openfiles'] = [abs_path]
                    else:
                        if abs_path not in statedict.dict['openfiles']:
                            print('opened file:', abs_path)
                            statedict.dict['openfiles'].append(abs_path)
                        else:
                            print('already open')
            elif command == 'closefile':
                if command_arg.isdigit():
                    if 'openfiles' in statedict.dict and int(command_arg) < len(statedict.dict['openfiles']):
                        abs_path = statedict.dict['openfiles'][int(command_arg)]
                        statedict.dict['openfiles'].remove(abs_path)
                        print('closed file:', abs_path)
                else:
                    abs_path = os.path.abspath(command_arg)
                    if 'openfiles' in statedict.dict:
                        if abs_path in statedict.dict['openfiles']:
                            statedict.dict['openfiles'].remove(abs_path)
                            print('closed file:', abs_path)
                        else:
                            print('file not open')
            elif command == 'openfiles?':
                if 'openfiles' in statedict.dict:
                    if len(statedict.dict['openfiles']) > 0:
                        print('open files:')
                        for i, file in enumerate(statedict.dict['openfiles']):
                            print(i, file)
                    else:
                        print('no files open')
                else:
                    print('no files open')
        else:
            print('command not found')
    else:
        last_node_id = handle_user_input(user_input, last_node_id)
    save_nodes()
    save_codeblocks()
    save_statedict()
    return True

# loop taking user input and generating response
def chat_loop():
    while True:
        if statedict.multiline == False:
            user_input = input('§ ')
        else:
            user_input_lines = []
            while True:
                user_input_line = input('§')
                if user_input_line == 'EOF':
                    break
                user_input_lines.append(user_input_line)
            user_input = '\n'.join(user_input_lines)
        if do_round(user_input) == False:
            break

if __name__ == '__main__':
    if not sys.stdin.isatty():  # Check if there is piped input
        print('piping')
        piped_input = sys.stdin.read()
        print('piped input:', piped_input)
        do_round(piped_input)
    else:
        if len(sys.argv) > 1:
            command_args = " ".join(sys.argv[1:])
            do_round(command_args)
        else:
            chat_loop()

