import os
import sys
import xml.etree.ElementTree as ET
from glob import glob

from galaxy.tool_util.parser import xml as galaxy_xml

import yaml


tool_repo_root = sys.argv[1]  # e.g. /home/user/GitRepos/tools-iuc/tools/
github_url = sys.argv[2].rstrip('/')  # e.g. https://raw.githubusercontent.com/galaxyproject/tools-iuc/master/tools
wrappers = glob(f"{tool_repo_root.rstrip('/')}/*/*xml")

test_data = {}
for wrapper in wrappers:
    wrapper_base_dir = '/'.join(wrapper.split('/')[:-1])
    if 'macro' in wrapper:
        continue
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
                        # print(el.get('element_definition', {}).get('value'))
                        if not el.get('element_definition', {}).get('value'):
                            continue
                        if os.path.exists(f"{wrapper_base_dir}/test-data/{el['element_definition']['value']}"):
                            test_inputs[el['element_definition']['name']] = f"{'/'.join((github_url, wrapper.split('/')[-2]))}/test-data/{el['element_definition']['value']}"
                else:
                    continue
            if os.path.exists(f"{wrapper_base_dir}/test-data/{inp['value']}"):
                test_inputs[inp['name']] = f"{'/'.join((github_url, wrapper.split('/')[-2]))}/test-data/{inp['value']}"
                wrapper_data[test_index] = test_inputs
    test_data['/'.join(wrapper.split('/')[-2:])] = wrapper_data

with open(f"{tool_repo_root.rstrip('/')}/test-data.yaml", 'w') as f:
    yaml.dump(test_data, f)
