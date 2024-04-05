import json

file_path = 'categories.json'

def read_category_data():
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def add_item_to_category(category, item):
    data = read_category_data(file_path)
    if category in data:
        if item not in data[category]:
            data[category].append(item)
    else:
        data[category] = [item]
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def write_categories(data):
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)