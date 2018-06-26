import csv
import sys

def value_for_type(value, value_type):
    if value.strip() in set(['', ';']):
        return None
    value = value.lower()
    if value_type in set(['num', 'number']):
        return float(value)
    if value_type in set(['str', 'string']):
        return value
    if value_type in set(['bool', 'boolean']):
        return value.lower() in set(['true', 't', 'yes', 'y'])
    if value_type in set(['list', 'array', 'arr']):
        return [x.strip() for x in value.strip().split(';')]
    return value

def read_def_csv(filename, dupes=False):
    rows = []
    with open(filename, 'r') as f:
        reader = csv.reader(f)
        for r in reader:
            rows.append(r)
    name_header = rows[0]
    type_header = rows[1]
    rows = rows[2:]
    defs = {}
    for row in rows:
        obj = {}
        for i in range(len(name_header)):
            v = value_for_type(row[i], type_header[i])
            if v != None:
                obj[name_header[i]] = v
        if obj['name'] not in defs:
            defs[obj['name']] = [] if dupes else None
        if dupes:
            defs[obj['name']].append(obj)
        else:
            defs[obj['name']] = obj
    return defs

def read_def_file(filename, dupes=False):
    if filename.endswith('csv'):
        return read_def_csv(filename, dupes)
    elif filename.endswith('json'):
        return read_def_json(filename, dupes)
    return None

def get_matching_adjective_item_defs(term):
    global adj_terms
    if term not in adj_terms:
        return None
    return adj_terms[term]

def get_core_item_def(term):
    global core_terms
    if term not in core_terms:
        return None
    return core_terms[term]

def compose_item_def(item_name):
    terms = item_name.strip().split()
    potential_item_defs = []
    for term in terms[:-1]:
        potential_item_defs.append(get_matching_adjective_item_defs(term))
        if not potential_item_defs[-1]:
            print('Definitions for item adjective "{0}" do not exist!'.format(term))
            return None
    core_item = get_core_item_def(terms[-1])
    if not core_item:
        print('Definition for core item "{0}" does not exist!'.format(terms[-1]))
        return None
    target_type = core_item['type']
    item_defs = []
    for options in potential_item_defs[::-1]:
        for option in options:
            if option['target_type'] == target_type:
                item_defs.append(option)
                target_type = option['type']
                break
            print('Adjective "{0}" does not apply to item "{1}"'.format('#TODO: indicate adj name', '#TODO: indicate so far compiled item name'))
            return None
    adj_defs = item_defs[::-1]  #  [x for x in item_defs if x['target_type'] == core_item['type']]
    
    if len(adj_defs) < len(terms)-1:
        print('That item does not exist (adjectives cannot apply to core item)')
        return None
    elif len(adj_defs) > len(terms)-1:
        print('That item does not exist (adjectives are somehow ambiguous with core item)')
        return None
    
    item = {}
    item['name'] = item_name
    item['type'] = adj_defs[0]['type']
    
    properties = set(core_item.keys())
    for adj in adj_defs:
        properties = properties.union(set(adj.keys()))
    properties = properties.difference(set(['target_type', 'name', 'type']))
    components = adj_defs+[core_item]
    for prop in properties:
        prop_types = set()
        prop_values = []
        for comp in components:
            if prop in comp:
                prop_types.add(str(type(comp[prop]))[8:-2])
                prop_values.append(comp[prop])
        if len(prop_types) > 1 and prop_types != set(['float', 'int']):
            raise ValueError('Mismatch of types for column "{0}" between item component definitions: {1}'.format(prop, [x['name'] for x in components]))
        prop_type = list(prop_types)[0]
        if prop_type in set(['float', 'int']):
            prop_value = 1
            for v in prop_values:
                prop_value *= v
        elif prop_type == 'str':
            prop_value = prop_values[0]
        elif prop_type == 'list':
            master_list = []
            for v in prop_values:
                master_list.extend(v)
            prop_value = [x for x in list(set(master_list)) if len(x)]
        elif prop_type == 'bool':
            prop_value = prop_values[0]
        else:
            raise ValueError('Invalid data type "{0}" found in column "{1}"'.format(prop_type, prop))
        item[prop] = prop_value
    return item

def main():
    global adj_terms
    global core_terms
    core_terms = read_def_file(sys.argv[1])
    adj_terms = {}
    for file in sys.argv[2:]:
        addl_adjs = read_def_file(file, True)
        for k in addl_adjs:
            if k not in adj_terms:
                adj_terms[k] = []
            adj_terms[k].extend(addl_adjs[k])
    print('definitions loaded!')
    while True:
        item_name = input('Enter an item name: ')
        item_def = compose_item_def(item_name)
        print(item_def)
        print()

if __name__ == "__main__":
    main()