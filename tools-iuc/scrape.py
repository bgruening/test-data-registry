import os
import sys
import xml.etree.ElementTree as ET
from glob import glob

from galaxy.tool_util.parser import xml as galaxy_xml

import requests
import yaml


def create_registry_entry(github_org, github_repo, tool_id, dataset_name, dataset_description, path, filetype, license, github_auth):
    """
    Returns an entry
    """
    github_metadata = requests.get(f"https://api.github.com/repos/{github_org}/{github_repo}/contents/tools/{path}/test-data/{dataset_name}", auth=tuple(github_auth.split(':'))).json()
    if github_metadata.get("errors") or github_metadata.get("message", "").startswith("API rate limit") or github_metadata.get("message", "").startswith("Not Found"):
        return {"data": {dataset_description}, "error": github_metadata["message"]}
    entry = {
        "doc": f"Test dataset {dataset_description} for {tool_id}.",
        "data": {
            dataset_description: {
                "location": github_metadata['download_url'],
                "sha": github_metadata["sha"],
                "unpack": False,  # TODO
                "filetype": filetype,
            },
        },
        "license": license,
        "size": github_metadata["size"],
        "used-by": tool_id,
    }
    return entry


tool_repo_root = sys.argv[1]  # e.g. /home/user/GitRepos/tools-iuc/tools/
github_org = sys.argv[2]  # e.g. galaxyproject
github_repo = sys.argv[3]  # e.g. tools-iuc
category = sys.argv[4]  # e.g. Assembly
github_auth = sys.argv[5]  # to avoid gh api rate limits. username:token
wrappers = [wrapper for wrapper in glob(f"{tool_repo_root.rstrip('/')}/*/*xml") if 'macro' not in wrapper]

test_data = []
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
                            test_data.append(create_registry_entry(github_org, github_repo, xml.parse_id(), el['element_definition']['value'], el['element_definition']['name'], wrapper_base_dir.split(tool_repo_root)[-1], el['element_definition']["attributes"].get("ftype"), "MIT", github_auth))
            else:
                if os.path.exists(f"{wrapper_base_dir}/test-data/{inp['value']}"):
                    test_data.append(create_registry_entry(github_org, github_repo, xml.parse_id(), inp['value'], inp['name'], wrapper_base_dir.split(tool_repo_root)[-1], inp["attributes"].get("ftype"), "MIT", github_auth))

with open(f"{tool_repo_root.rstrip('/')}/test-data.yaml", 'w') as f:
    yaml.dump(test_data, f)
