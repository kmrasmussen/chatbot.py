import os
model = 'openai/gpt-3.5-turbo' #'openai/gpt-4-turbo' #'mistralai/mixtral-8x7b'
nodes_pickle_filename = 'nodes.pkl'
codeblocks_pickle_filename = 'codeblocks.pkl'
statedict_pickle_filename = 'statedict.pkl'
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
USE_REDIS_CLIPBOARD = True
USE_TOOLS = True
TOOLS_PROMPT_FILENAME = '/home/ec2-user/projects/chatbot.py/prompts/tooldescriptions.md'