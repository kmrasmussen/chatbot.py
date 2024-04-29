# if the markdown contains code blocks with the format ```<language>
# then insert "(copy <number>)" after ```<language> to allow copying the code
# this means it should happen for all code blocks.
# the function returns the modified response_text and a list of all the code blocks
# as strings of the code inside the blocks
def add_code_copy_tag_to_response_text(response_text, code_blocks_start_index=0):
    code_blocks = []
    code_block_start = False
    code_block = ''
    response_text_with_copy_tags = ''
    for line in response_text.split('\n'):
        if line.strip().startswith('```'):
            if code_block_start:
                code_blocks.append(code_block.strip())
                response_text_with_copy_tags += line + f'(cp {code_blocks_start_index + len(code_blocks) - 1})\n'
                code_block = ''
                code_block_start = False
            else:
                code_block_start = True
                response_text_with_copy_tags += line + f'(cp {code_blocks_start_index + len(code_blocks)})\n'
        else:
            if code_block_start:
                code_block += line + '\n'
            response_text_with_copy_tags += line + '\n'
    return response_text_with_copy_tags, code_blocks


'''
# read text
with open('codeblocks.md', 'r') as file:
    response_text = file.read()

response_text_with_copy_tags, code_blocks = add_code_copy_tag_to_response_text(response_text)
print(response_text_with_copy_tags)
print(code_blocks)
'''