import os
import sys
import xml.etree.ElementTree as ET
from glob import glob

from galaxy.tool_util.parser import xml as galaxy_xml

import requests

import yaml


def create_registry_entry(github_org, github_repo, tool_ids, dataset_identifier, filetype, edams, license, github_auth):
    """
    Returns an entry
    """
    path, filename = dataset_identifier.split('__')
    auth = tuple(github_auth.split(':'))
    try:
        github_metadata = requests.get(f"https://api.github.com/repos/{github_org}/{github_repo}/contents/tools/{path}/test-data/{filename}", auth=auth, timeout=10).json()
    except requests.exceptions.ConnectTimeout:
        return {"data": {dataset_identifier}, "error": "timeout"}
    if github_metadata.get("errors") or github_metadata.get("message", "").startswith("API rate limit") or github_metadata.get("message", "").startswith("Not Found"):
        return {"data": {dataset_identifier}, "error": github_metadata["message"]}
    entry = {
        "doc": "Placeholder doc",
        "data": {
            dataset_identifier: {
                "location": github_metadata['download_url'],
                "sha": github_metadata["sha"],
                "unpack": False,  # TODO
                "filetype": filetype,
            },
        },
        "license": license,
        "size": github_metadata["size"],
        "used-by": list(tool_ids),
        "edams": list(edams),
    }
    return entry


def update_test_data_dict(test_data, tool_edams, dataset_identifier, tool_id, dataset_description, ftype):
    """
    update test_data dict with a new entry
    """
    edams = tool_edams.get(tool_id, set())
    if dataset_identifier in test_data:
        test_data[dataset_identifier]['tool_ids'].add(tool_id)
        test_data[dataset_identifier]['edams'].update(edams)
    else:
        test_data[dataset_identifier] = {'tool_ids': {tool_id}, 'ftype': ftype, 'edams': edams}


def get_edam_from_xml(xml_tool_source):
    """
    Get EDAM topics from an XmlToolSource object
    """
    edams = set()

    # first, get directly annotated
    edams.update([topic.split('_')[-1] for topic in xml_tool_source.parse_edam_topics()])

    # second, check biotools
    xrefs = xml_tool_source.parse_xrefs()
    if xrefs:
        for xref in xrefs:
            if xref.get('reftype') == 'bio.tools':
                api_req = requests.get(f"https://bio.tools/api/tool/{xref.get('value')}", params={'format': 'json'}).json()
                edams.update([topic['uri'].split('_')[-1] for topic in api_req.get('topic', [])])

    return edams


tool_repo_root = sys.argv[1]  # e.g. /home/user/GitRepos/tools-iuc/tools/
github_org = sys.argv[2]  # e.g. galaxyproject
github_repo = sys.argv[3]  # e.g. tools-iuc
category = sys.argv[4]  # e.g. Assembly
github_auth = sys.argv[5]  # to avoid gh api rate limits. username:token
wrappers = [wrapper for wrapper in glob(f"{tool_repo_root.rstrip('/')}/*/*xml") if 'macro' not in wrapper]

test_data = {}
tool_edams = {}
for wrapper in wrappers:
    wrapper_base_dir = '/'.join(wrapper.split('/')[:-1])
    with open(f"{wrapper_base_dir}/.shed.yml") as f:
        if category not in yaml.load(f, Loader=yaml.SafeLoader).get('categories', []):
            continue
        # else: open the wrapper if the category matches

    tree = ET.parse(wrapper)
    wrapper_data = {}
    test_inputs = {}
    try:
        xml = galaxy_xml.XmlToolSource(tree, macro_paths=glob(f"{wrapper_base_dir}/*"))
        tests = xml.parse_tests_to_dict()['tests']
    except Exception as e:
        print(f"Exception raised while reading {wrapper}: {e}")
        continue
    tool_edams[xml.parse_id()] = get_edam_from_xml(xml)
    for test_index, test in enumerate(tests):
        for inp in test['inputs']:
            if not inp.get('value'):
                # test for collections
                if inp.get('attributes', {}).get('collection'):
                    collection = inp['attributes']['collection'].to_dict()
                    for el in collection.get('elements', []):
                        if not el.get('element_definition', {}).get('value'):
                            continue
                        if os.path.exists(f"{wrapper_base_dir}/test-data/{el['element_definition']['value']}"):
                            dataset_identifier = '__'.join((wrapper_base_dir.split(tool_repo_root)[-1], el['element_definition']['value']))
                            update_test_data_dict(test_data, tool_edams, dataset_identifier, xml.parse_id(), el['element_definition']['name'], el['element_definition']["attributes"].get("ftype") or el['element_definition']['value'].split('.')[-1])

            else:
                if os.path.exists(f"{wrapper_base_dir}/test-data/{inp['value']}"):
                    dataset_identifier = '__'.join((wrapper_base_dir.split(tool_repo_root)[-1], inp['value']))
                    update_test_data_dict(test_data, tool_edams, dataset_identifier, xml.parse_id(), inp['name'], inp["attributes"].get("ftype") or inp['value'].split('.')[-1])

registry = []

for dataset_identifier, dat in test_data.items():
    registry.append(create_registry_entry(github_org, github_repo, dat['tool_ids'], dataset_identifier, dat["ftype"], dat["edams"], "MIT", github_auth))

with open(f"{tool_repo_root.rstrip('/')}/test-data.yaml", 'w') as f:
    yaml.dump(registry, f)
