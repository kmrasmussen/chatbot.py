import re
import xml.etree.ElementTree as ET

def extract_xml_structures(input_string):
    pattern = r'<(\w+)(?:>(.*?)</\1>|/>)'  # Updated pattern to handle empty tags
    matches = re.findall(pattern, input_string)
    
    result = []
    for match in matches:
        tag, content = match
        element = {
            'tag': tag,
            'content': content.strip()
        }
        result.append(element)
    
    return result

def extract_xml_actions(document: str):
    # Define the regex pattern to find <action> tags and their contents
    pattern = r"<action>.*?</action>"
    
    # Find all matches in the document
    matches = re.findall(pattern, document, re.DOTALL)
    
    return matches

def escape_content(content):
    print('escaping inspect', repr(content))
    # replace literal backslash-backslash-n with real backslash-n
    content = content.replace('\\n', '')
    print('escaping inspect 2', repr(content))
    return content

def xml_action_to_dict2(xml_action: str):

    # Initialize an empty dictionary to hold the action elements
    action_dict = {}

    # Extract the action content between <action> and </action>
    action_content = xml_action.split('<action>')[1].split('</action>')[0].strip()

    # Split the content into lines and process each line
    for line in action_content.split('\n'):
        line = line.strip()
        if line.startswith('<') and line.endswith('>'):
            # Extract the tag and the content
            tag = line.split('>')[0][1:]
            content = line.split('>')[1].split('<')[0]
            action_dict[tag] = content
    print('dict2')
    return action_dict

def xml_action_to_dict(xml_action: str):
    print('xml action to dict')
    print('pre', xml_action)
    xml_action = escape_content(xml_action)
    print('post', xml_action)

    # Parse the XML string
    root = ET.fromstring(xml_action.replace('\\n', 'newline'))
    
    # Create a dictionary from the XML elements
    action_dict = {child.tag: child.text for child in root}
    
    return action_dict

def xml_action_to_dict3(xml_action: str):
    print('dict3', repr(xml_action))
    # Initialize an empty dictionary to hold the action elements
    action_dict = {}

    from lxml import etree
    parser = etree.XMLParser(recover=True)
    root = etree.fromstring(xml_action, parser=parser)
    # Parse the XML string
    #root = ET.fromstring(xml_action.strip())

    # Iterate through child elements of <action>
    for child in root:
        action_dict[child.tag] = child.text.strip() if child.text else ""

    return action_dict

def extract_actions_dicts(document: str):
    return [xml_action_to_dict3(action) for action in extract_xml_actions(document)]