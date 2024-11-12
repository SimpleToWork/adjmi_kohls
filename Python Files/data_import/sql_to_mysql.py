import os
import sys

currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
from data_recruit import DataRecruitApi


def pull_and_import_data(data_api, data_type, export_folder, drop_table,delete_columns=[], delete_settings=[], delete_operators=[], delete_values=[]):
    if data_type == 'style_master':
        script = f'''Select row_number() over (partition by '' order by style_key) as product_id, 'X' as static, 
            'Active' as Status, 'Adjmi Apparel' as Account_Name,
            A.* from style_master A;'''
    if data_type == 'style_carton_master':
        script = f'''Select  'Adjmi Apparel' as Account_Name,'X' as static,
                   A.* from style_carton_master A;'''

    if data_type == 'production_order_master':
        script = f'''Select  'Adjmi Apparel' as Account_Name,'X' as static,
                      A.* from production_order_master A;'''

    table_name = data_type.replace(" ","_")
    df = data_api.recruit_data_sets(data_type=data_type, sql_server_script=script)
    data_api.export_data_to_file(export_folder=export_folder, filename=data_type, file_type='csv', data_type=data_type,
                               df=df)
    data_api.import_data_locally(data_type=data_type, dataframe=df, table_name=table_name, drop=drop_table,
                               delete_columns=delete_columns, delete_settings=delete_settings,
                               delete_operators=delete_operators, delete_values=delete_values)



def migrate_data(sql_engine, mysql_engine, project_name, export_folder):
    data_api = DataRecruitApi(sql_engine=sql_engine, mysql_engine=mysql_engine, project_name=project_name)
    # pull_and_import_data(data_api=data_api, data_type='style_master', export_folder=export_folder, drop_table=True)
    # pull_and_import_data(data_api=data_api, data_type='style_carton_master', export_folder=export_folder, drop_table=True)
    pull_and_import_data(data_api=data_api, data_type='production_order_master', export_folder=export_folder,
                         drop_table=True)