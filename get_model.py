import os
from subprocess import check_output
from pyinaturalist.node_api import get_taxa, get_taxa_by_id

def launch_inaturalist(model):
    obj_result = check_output(["python3", "inaturalist_classification.py", "-i", "foo.jpg", "-m",  model])
    #return output.decode()
    obj_result = obj_result.decode()
    scientific_name = obj_result.split(':')[1].split('(')[0].strip()
    common_name = obj_result.split('(')[1].split(')')[0].strip()
    return [scientific_name, common_name]
    
def search_inaturalist(model_arr):
    #foo_outbrackets = model_name.split(':')[1].split('(')[0].strip()
    #foo_inbrackets = model_name.split('(')[1].split(')')[0].strip()
    
    foo_outbrackets = model_arr[0]
    foo_inbrackets = model_arr[1]
    
    response = get_taxa(q=foo_inbrackets) # 712366 or 544795
    response = ({taxon["id"]: taxon["name"] for taxon in response["results"]})
    
    foo = None
    for num, name in response.items():
        if name == foo_outbrackets or name == foo_inbrackets:
            foo = num
            
    
    response = get_taxa_by_id(foo) # only the id number
    basic_fields = ["wikipedia_summary"] # check for other arguements


    foo_info = response["results"][0]["wikipedia_summary"]
    return foo_info    
