from subprocess import check_output
from pyinaturalist.node_api import get_taxa, get_taxa_by_id

def launch_inaturalist(model):
    # launches object identifier with given parameters, and returns the scientic and common name of the object
    obj_result = check_output(["python3", "inaturalist_classification.py", "-i", "foo.jpg", "-m",  model])
    obj_result = obj_result.decode()
    scientific_name = obj_result.split(':')[1].split('(')[0].strip()
    common_name = obj_result.split('(')[1].split(')')[0].strip()
    return [scientific_name, common_name]
    
def search_inaturalist(model_arr):
    # searches iNaturalist database of given names and return information and wiki url
    foo_outbrackets = model_arr[0]
    foo_inbrackets = model_arr[1]
    
    response = get_taxa(q=foo_inbrackets)
    response = ({taxon["id"]: taxon["name"] for taxon in response["results"]})
    
    foo = None
    for num, name in response.items():
        if name == foo_outbrackets or name == foo_inbrackets:
            foo = num
    
    response = get_taxa_by_id(foo) # only the id number

    foo_info = response["results"][0]["wikipedia_summary"]
    foo_url = response["results"][0]["wikipedia_url"]
    return foo_info, foo_url
