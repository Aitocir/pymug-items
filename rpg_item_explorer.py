import csv
import json
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
    print('composing {0}...\n'.format(item_name))
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
    elif len(terms) == 1:
        return core_item
    target_type = core_item['type']
    item_defs = []
    progressive_name = []
    for options in potential_item_defs[::-1]:
        found_one = False
        for option in options:
            if option['target_type'] == target_type:
                item_defs.append(option)
                target_type = option['type']
                progressive_name.append(option['name'])
                found_one = True
                break
        if not found_one:
            print('Adjective "{0}" does not apply to item "{1}"'.format(options[0]['name'], ' '.join(progressive_name[::-1])))
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

def read_recipe_file(filename):
    with open(filename) as f:
        text = f.read()
    try:
        body = json.loads(text)
        return body
    except:
        print('Recipe file "{0}" contains invalid JSON'.format(filename))
        return []

def possible_recipe_signatures(items, counts):
    sigs = []
    item_lists = []
    for i in range(len(items)+1):
        sig = []
        for j in range(len(items)):
            if j < i:
                sig.append((items[j]['name'], counts[j], items[j]))
            else:
                sig.append((items[j]['type'], counts[j], items[j]))
        sig = sorted(sig)
        sigs.append(';'.join([x[0]+':'+str(x[1]) for x in sig]))
        item_lists.append([x[2] for x in sig])
    return sigs[::-1], item_lists[::-1]

def process_recipe(recipe, items):
    #  TODO: random, skill, tool, all the fancy stuff really
    output = {}
    for item in recipe['success']:
        if ';' in item:
            pattern, args = item.split(';')
            args = args.split(',')
            params = []
            for a in args:
                name, idx = a.split(':')
                i = items[recipe['itemrefs'].index(name)]
                print(i)
                print(i['name'])
                params.append(i['name'].split()[::-1][int(idx)])
            output[pattern.format(*params)] = recipe['success'][item]
        else:
            output[item] = recipe['success'][item]
    return output

def main():
    #
    #  Load item definitions
    #
    global adj_terms
    global core_terms
    core_terms = read_def_file(sys.argv[1])
    adj_terms = {}
    for file in sys.argv[2:3]:
        addl_adjs = read_def_file(file, True)
        for k in addl_adjs:
            if k not in adj_terms:
                adj_terms[k] = []
            adj_terms[k].extend(addl_adjs[k])
    print('item definitions loaded!')
    #
    #  Load recipe definitions
    #
    global recipes
    recipes = {}
    for file in sys.argv[3:4]:
        addl_recipes = read_recipe_file(file)
        #  TODO: re-package recipes into cache format and store
        for r in addl_recipes:
            recipe = {}
            statics = [(x, r['specific-ingredients'][x]) for x in r['specific-ingredients']]
            vars = [(x, r['typed-ingredients'][x]) for x in r['typed-ingredients']]
            ingredients = sorted(statics+vars)
            recipe['signature'] = ';'.join([x[0]+':'+str(x[1]) for x in ingredients])
            recipe['itemrefs'] = [x[0] for x in ingredients]
            recipe['constants'] = statics
            recipe['variables'] = vars
            recipe['success'] = r['success'] if 'success' in r else {}
            recipe['failure'] = r['failure'] if 'failure' in r else {}
            recipe['success_xp'] = r['success_xp'] if 'success_xp' in r else {}
            recipe['failure_xp'] = r['failure_xp'] if 'failure_xp' in r else {}
            recipe['tool'] = r['tool'] if 'tool' in r else False
            recipe['random'] = r['random'] if 'random' in r and 0<r['random']<1 else 1
            if 'skill' not in r:
                recipe['skill_name'] = None
            else:
                try:
                    recipe['skill_name'] = r['skill']['name']
                    recipe['skill_min'] = r['skill']['min'] if 'min' in r['skill'] else 0
                    recipe['skill_max'] = r['skill']['mastery'] if 'mastery' in r['skill'] else 2**31
                    recipe['skill_step'] = r['skill']['step'] if 'step' in r['skill'] else 1
                    recipe['skill_f'] = r['skill']['stepexp'] if 'stepexp' in r['skill'] else 1
                except:
                    print('Recipe has missing fields from its skill!')
                    continue
            if recipe['signature'] in recipes:
                print('Recipe being overridden!\nOld: {0}\nNew: {1}'.format(recipes[recipe['signature']], recipe))
            recipes[recipe['signature']] = recipe
    print('recipe definitions loaded!')
    #
    #  Interpreter loop
    #
    while True:
        user_input = input('pymug-items> ')
        cmd = user_input.split()[0]
        if cmd == 'check':
            item_name = ' '.join(user_input.split()[1:])
            item_def = compose_item_def(item_name)
            print(item_def)
            print()
        elif cmd == 'craft':
            items_text = user_input[len(cmd):].strip()
            item_descs = [x.strip().split(':') for x in items_text.split(';')]
            items = [compose_item_def(x[0]) for x in item_descs]
            counts = [x[1] for x in item_descs]
            if None in items:
                print('one of your items is not real!\n')
                continue
            possible_recipes, item_lists = possible_recipe_signatures(items, counts)
            for i in range(len(possible_recipes)):
                sig = possible_recipes[i]
                item_list = item_lists[i]
                if sig in recipes:
                    #print(recipes[sig]['success'])
                    print(process_recipe(recipes[sig], item_list))
                    print()

if __name__ == "__main__":
    main()