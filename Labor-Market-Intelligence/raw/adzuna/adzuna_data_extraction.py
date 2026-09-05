import json
import re
from os import path
import glob
import csv


base_folder = path.dirname(__file__)
json_path_list = glob.glob(f'{base_folder}/*.json')
completed_files = path.join(base_folder,'completed_files.txt')
csv_path = path.join(base_folder,'adzuna_extracted.csv')
dimensions_table = path.join(base_folder,'..','tech_dimension_table.json')

def data_for_csv(file,csv_path,ref_table):
    with open(file,'r') as f:
        raw_data = json.load(f)

    output = []
    for data in raw_data:

        if data['id'] in unique_ids:
            continue

        tech_string = ''

        date = data['created']
        title = data['title']
        description = data['description']
        job = title + ' ' +description
        transform = re.sub(r'[^A-Z #+]', ' ',job.upper())

        for techs in ref_table:
            tech = techs['Adzuna']
            pattern = r'\b'+ re.escape(tech) + r'\b'
            if re.search(pattern,transform):
                tech_string += tech + ','

        row = [data['id'], date[:10], tech_string]

        output.append(row)


    with open(csv_path,'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            unique_ids.add(int(row['ID']))
    
    return output


if __name__ == '__main__':

    unique_ids = set()
    with open(dimensions_table,'r') as f:
        dim_table = json.load(f)
    if not path.exists(csv_path) or path.getsize(csv_path)==0:
        with open(csv_path, 'a', newline = '') as f:
            header = ['ID','Created','Technologies']
            writer = csv.writer(f)
            writer.writerow(header)
            for json_file in json_path_list:
                writer.writerows(data_for_csv(json_file,csv_path,dim_table))
    
    else:
        
        with open(completed_files,'r') as f:
            files = {item.strip() for item in f}
        with open(csv_path,'a', newline = '') as f:
            writer = csv.writer(f)

            for json_file in json_path_list:
                if not json_file in files:
                    writer.writerows(data_for_csv(json_file,csv_path,dim_table))