import itertools

def url_builder(base_url, slash_list=[]):
    """Expected strings in slash list (potentially will be extended to dicts)"""
    url = base_url
    if url[-1] == '/':
        url = url[:-1]
    for slash in slash_list:
        url += '/' + slash
    return url

def urls_builder(base_url, slash_elements_list = [], zipped = True, all_combinations = False):
    """expecting list of lists"""
    urls = []
    if zipped:
        if all_combinations:
            slash_lists = list(set(itertools.product(*slash_elements_list)))
        else:
            slash_lists = list(zip(*slash_elements_list))
    else:
        
        slash_lists = slash_elements_list
    for slash_list in slash_lists:
            urls.append(url_builder(base_url, slash_list))
    return urls