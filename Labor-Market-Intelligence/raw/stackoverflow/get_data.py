from requests import get
import pandas as pd
import os

url = 'https://media.githubusercontent.com/media/StackExchange/Survey/refs/heads/main/packages/archive/2025/results.csv'
get_obj = get(url)

output_path = os.path.join(os.path.dirname(__file__),'survey_result.csv')
with open(output_path, 'wb') as result_file:
    result_file.write(get_obj.content)
