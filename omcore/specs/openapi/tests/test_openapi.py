from .... import lang
from .... import marshal as msh
from ....formats.json import all as json
from ....formats.yaml import all as yaml
from ..openapi import Openapi


def test_openapi():
    yml_src = lang.get_relative_resources('.', globals=globals())['example.yml'].read_bytes().decode('utf-8')
    doc = yaml.loads(yml_src)

    api = msh.unmarshal(doc, Openapi)

    print(json.dumps_pretty(msh.marshal(api)))
