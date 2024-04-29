import subprocess
from uuid import uuid4
from os.path import exists, join
from time import sleep
import time
import json
import re
import redis

class AgentShell:
    def __init__(self, cwd=None, redis_pubsub_channel=None, redis_client=None):
        # Open the output file in append mode so that each command's output is added to the end of the file
        # the output file is created as a temporary file
        # erase out.txt and in.jsonl files if they exist
        if exists('out.txt'):
            open('out.txt', 'w').close()
        if exists('in.jsonl'):
            open('in.jsonl', 'w').close()        
        self.output_file = open('out.txt', 'a')
        self.input_file = open('in.jsonl', 'a')
        self.input_list = []
        self.output_list = []
        # Start a subprocess with a shell, directing stdout and stderr to the same output file
        if cwd is not None:
            assert exists(cwd), "The specified AgentShell cwd (work directory) does not exist"
        self.process = subprocess.Popen(["/bin/bash"], stdin=subprocess.PIPE, stdout=self.output_file, stderr=subprocess.STDOUT, text=True, cwd=cwd)
        #use python3 instead
        #self.process = subprocess.Popen(["python3"], stdin=subprocess.PIPE, stdout=self.output_file, stderr=subprocess.STDOUT, text=True)
        if redis_pubsub_channel:
            # redis pubsub will only be used for publishing not for subscribing
            self.redis_pubsub_channel = redis_pubsub_channel
            assert redis_client is not None, "redis_client must be provided if redis_pubsub_channel is provided"
            self.redis = redis_client
            #print('agentshell redis channel:', self.redis_pubsub_channel)
        else:
            self.redis_pubsub_channel = None
            self.redis = None
            #print('no agentshell redis channel used')
        # make uuid4 for the shell object itself
        self.shell_id = str(uuid4())
            
    def get_command_output_list(self, merge_orphans=False):
        output_list = []
        with open('out.txt', 'r') as file:
            current_command_id = None
            command_is_open = False
            open_command_content = ''
            for line in file:
                # if line is a start delimiter of format ---uuid--- using regex
                line_is_start = re.match(r'---[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}---', line)
                line_is_end = re.match(r'///[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}///', line)
                if line_is_start:
                    current_command_id = line.strip()[3:-3]
                    print('current_command_id:', current_command_id)
                    command_is_open = True
                elif line_is_end:
                    line_end_current_command_id = line.strip()[3:-3]
                    assert current_command_id == line_end_current_command_id, "Command start and end delimiter mismatch"
                    command_output_dict = {
                        "command_id": current_command_id,
                        "output": open_command_content
                    }
                    output_list.append(command_output_dict)
                    open_command_content = ''
                    command_is_open = False
                elif command_is_open:
                    open_command_content += line
                    print('open_command_content:', open_command_content)
                else:
                    print('orphan: line is not part of any command:', line, 'previous command:', output_list[-1]['command_id'])
                    if merge_orphans:
                        output_list[-1]['output'] += line
                    else:
                        raise Exception('Orphan line found')
            input_list_command_ids = [command['command_id'] for command in self.input_list]
            output_list_command_ids = [command['command_id'] for command in output_list]    
            if command_is_open:
                print('command not closed')
                assert len(self.input_list) > len(output_list), "Failed assertion that input list is longer than output list when last command not closed"
                assert len(self.input_list) == len(output_list) + 1, "Failed assertion that input list is one longer than output list when last command not closed"
                assert input_list_command_ids[:-1] == output_list_command_ids, "Failed assertion that input list command ids are the same as output list command ids when last command not closed"
            else:
                assert input_list_command_ids == output_list_command_ids, "Failed assertion that input list command ids are the same as output list command ids"
        return output_list, command_is_open

    def get_completed_pairs(self):
        input_list_command_ids = [command['command_id'] for command in self.input_list]
        output_list_command_ids = [command['command_id'] for command in self.output_list]    
        assert input_list_command_ids == output_list_command_ids, "Failed assertion that input list command ids are the same as output list command ids"
        combined = [
            {
                "command_id": input_command['command_id'],
                "input": input_command['command_input'],
                "output": output_command['command_output'],
                "timestamp_input": input_command['timestamp'],
                "timestamp_output": output_command['timestamp']
            } for input_command, output_command in zip(self.input_list, self.output_list)
        ]
        return combined

    def get_completed_pairs_xml(self):
        completed_pairs = self.get_completed_pairs()
        '''
        formats it in the following way:
        <stdin> command input text is here </stdin>
        <stdout> command input text is here <stdout>
        <stdin> next command is here </stdin>
        <stdout> next command is here <stdout>
        '''
        xml = ''
        for pair in completed_pairs:
            xml += f'<stdin>{pair["input"]}</stdin>\n'
            xml += f'<stdout>{pair["output"]}</stdout>\n'
        return xml
        

    def execute_command(self, command):
        command_id = str(uuid4())
        # write the command to the input file with command delimiter
        input_command_dict = {
            "command_id": command_id,
            "command_input": command,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) 
        }
        self.input_file.write(json.dumps(input_command_dict) + "\n")
        self.input_file.flush()
        self.input_list.append(input_command_dict)
        #print('input_list:', self.input_list)

        #print('execute_command start')
        # Write the command to the subprocess stdin, appending newline to execute it
        self.add_line(f'---{command_id}---')
        #self.process.stdin.write(f'echo "---{command_id}---"' + "\n")
        #self.process.stdin.flush()
        
        self.process.stdin.write(command + "\n")
        self.process.stdin.flush()

        #sleep(1.0)
        # instead of waiting for 1.0 second for the file to not have changed for 100ms
        current_content = open('out.txt', 'r').read()
        while True:
            sleep(0.1)
            new_content = open('out.txt', 'r').read()
            if new_content == current_content:
                break
            current_content = new_content


        self.add_line(f'///{command_id}///')
        #self.process.stdin.write(f'echo "///{command_id}///"' + "\n")
        #self.process.stdin.flush()
        #print('execute_command end')
        return command_id

    def round_trip(self, command, sleep_interval=0.1):
        command_id = self.execute_command(command)
        output = self.read_output(command_id)
        while output is None:
            # Wait for 100 ms
            sleep(sleep_interval)
            output = self.read_output(command_id)
        roundtrip_dict = {
            "command_id": command_id,
            "command_input": command,
            "command_output": output.strip(),
            "shell_id": self.shell_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }
        self.output_list.append(roundtrip_dict)
        assert len(self.input_list) == len(self.output_list), "Failed assertion that input list is the same length as output list"
        input_list_command_ids = [command['command_id'] for command in self.input_list]
        output_list_command_ids = [command['command_id'] for command in self.output_list]    
        assert input_list_command_ids == output_list_command_ids, "Failed assertion that input list command ids are the same as output list command ids"
        if self.redis_pubsub_channel and self.redis:
            #print('SHELL PUBLISHING')
            self.redis.publish(self.redis_pubsub_channel, json.dumps(roundtrip_dict))
        return roundtrip_dict

    # reads the output file and finds the output of the command with the given command_id
    def read_output(self, command_id):
        #print('red_output start')
        #print('printall:')
        output_text = ''
        # First print everything in the output file
        got_to_start = False
        with open('out.txt', 'r') as file:
            for line in file:
                if line == f"---{command_id}---\n":
                    #print('THIS IS START!')
                    got_to_start = True
                elif line == f"///{command_id}///\n":
                    #print('THIS IS END!')
                    return output_text
                elif got_to_start:
                    output_text += line
        return None

    def add_line(self, line, command_id=None):
        # writes a line to out.txt file
        with open('out.txt', 'a') as file:
            file.write("\n" + line + "\n")

    def close(self):
        # Close the subprocess stdin and the output file when done
        self.process.stdin.close()
        self.output_file.close()

# thread that continually reads the output file and updates the output history

# Example usage
if __name__ == "__main__":
    tw = AgentShell()
    try:
        print("Terminal Wrapper: Type your command and press enter. Type 'exit' to quit.")

        while True:
            command_input = input("$ ")
            if command_input.strip().lower() == "exit":
                print("Exiting Terminal Wrapper.")
                break
            roundtrip_dict = tw.round_trip(command_input)
            command_id = roundtrip_dict['command_id']
            command_output = roundtrip_dict['command_output']
            print('%', command_id)
            print(command_output)

    finally:
        # Ensure resources are cleaned up properly
        tw.close()
    
    print(tw.get_completed_pairs_xml())
