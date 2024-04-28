#!/usr/bin/env python3

import os
import requests
import json 
import re
from os.path import exists, join
from colorama import Fore, Style
from codeblocks import add_code_copy_tag_to_response_text

model = 'openai/gpt-3.5-turbo' #'mistralai/mixtral-8x7b'
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
if not exists('blocks.txt'):
    with open('blocks.txt', 'w') as f:
        f.write('')

# function that adds a string to blocks.txt
def add_block_to_file(block):
    with open('blocks.txt', 'a') as f:
        f.write(block + '\n')

def get_completion(messages, model, or_api_key, add_assistant_response=True):
    #print('get response start', messages)
    response = requests.post(
    url="https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {or_api_key}",
    },
    data=json.dumps({
        "model": model, #"openai/gpt-3.5-turbo", # Optional'anthropic/claude-3-opus', #
        "messages": messages
    })
    )
    data = response.json()
    #print('data', data)
    assert len(data['choices']) == 1, 'Expected one choice'
    response_text = data['choices'][0]['message']['content']
    #print('res text', response_text)
    #print('get reponse end')
    if add_assistant_response:
        messages.append({
            "role": "assistant",
            "content": response_text
        })
    return response_text

command_list = ['exit', 'cp', 'clear']

# loop taking user input and generating response
def chat_loop():
    messages = []
    all_code_blocks = []
    while True:
        user_input = input('§ ')
        
        # check if user input is a command
        if user_input.startswith('!'):
            # command is the first word after ! until space, the argument string is the rest
            command = user_input[1:].split(' ')[0]
            command_arg = user_input[1 + len(command):].strip()
            print('command', command, 'arg', command_arg)
            if command in command_list:
                if command == 'exit':
                    break
                elif command == 'cp':
                    # copy the code block to clipboard
                    print('cp', int(command_arg))
                    print(all_code_blocks[int(command_arg)])
                elif command == 'clear':
                    messages = []
                    all_code_blocks = []
                continue

        messages.append({
            "role": "user",
            "content": user_input
        })
        response_text = get_completion(messages, model, OPENROUTER_API_KEY)
        response_text_with_copy_tags, code_blocks = add_code_copy_tag_to_response_text(response_text, len(all_code_blocks))
        all_code_blocks += code_blocks
        for block in code_blocks:
            add_block_to_file(block)
        print(Fore.WHITE + response_text_with_copy_tags)
        print(Style.RESET_ALL)


chat_loop()