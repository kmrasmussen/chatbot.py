#!/usr/bin/env python3
import readline
import os
from os.path import exists, join
from colorama import Fore, Style
from codeblocks import add_code_copy_tag_to_response_text
import pyperclip
from uuid import uuid4
import pickle

from config import *
from state import *
from agentshell import AgentShell
from completion import get_completion

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


def save_nodes():
    nodes.save_as_pickle(nodes_pickle_filename)
def save_codeblocks():
    codeblocks.save_as_pickle(codeblocks_pickle_filename)


# function that adds a string to blocks.txt
def add_block_to_file(block):
    with open('blocks.txt', 'a') as f:
        f.write(block + '\n')

command_list = ['exit', 'cp', 'clear', 'x', 'prefixshow', 'sethead', 'bash', 'bbash', 'lbp']

def handle_user_input(user_input, last_node_id):
    user_node = nodes.add_node(last_node_id, user_input, 'user')
    response_text = get_completion(nodes.get_messages(), 
                                   model,
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
    if user_input.startswith('!'):
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
                print(codeblock)
                pyperclip.copy(codeblock)
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
        else:
            print('command not found')
    else:
        last_node_id = handle_user_input(user_input, last_node_id)
    save_nodes()
    save_codeblocks()
    return True

# loop taking user input and generating response
def chat_loop():
    while True:
        user_input = input('§ ')
        if do_round(user_input) == False:
            break


import sys

if len(sys.argv) > 1:
    command_args = " ".join(sys.argv[1:])
    # Process the command-line arguments
    #print("Command Arguments:", command_args)
    do_round(command_args)
else:
    chat_loop()
