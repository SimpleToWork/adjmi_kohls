import os
import time
import sys
import getpass
import pandas as pd
from sqlalchemy import inspect
currentdir = os.path.dirname(os.path.realpath(__file__))
parentdir = os.path.dirname(currentdir)
sys.path.append(parentdir)
import time
from global_modules import print_color, engine_setup, create_folder, run_sql_scripts, Get_SQL_Types, Change_Sql_Column_Types, Add_Sql_Missing_Columns


class DataRecruitApi():
    def __init__(self, sql_engine, mysql_engine, project_name):
        self.sql_engine = sql_engine
        self.mysql_engine = mysql_engine
        self.project_name = project_name

    def recruit_data_sets(self, data_type='name of query', sql_server_script='query'):
        start_time = time.time()
        print_color(f'Attempting to Recruit data for {data_type}', color='y')
        print_color(f'Query: {sql_server_script}', color='p')
        df = pd.read_sql(sql_server_script, con=self.sql_engine)
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        print_color(df, color='b')
        print_color(f'Data for {data_type} Recruited. Took {round(time.time() - start_time,2)} Seconds To Pull. Total {df.shape[0]} Rows.', color='g')
        return df

    def export_data_to_file(self, export_folder, filename, file_type,  data_type, df):
        extended_filename = f'{export_folder}\\{filename}.{file_type}'
        df.to_csv(extended_filename, index=False)
        print_color(f'File for {data_type} Exported to: {extended_filename}', color='p')

    def import_data_locally(self, data_type, dataframe, table_name, drop=False, delete_columns=[], delete_settings=[], delete_operators=[], delete_values=[]):
        '''
        can either drop a table and re-push or
        can delete specific data from the table.
        see examples below

        :param data_type:
        :param dataframe:
        :param table_name:
        :param drop:
        :param delete_columns: ['size_code', 'size']
        :param delete_settings: ['AND']
        :param delete_operators: ["=", "IN"]
        :param delete_values: ["13", ["ppk", "xsb"]]
        :return:
        '''
        if drop is True:
            scripts=[f'Drop Table if exists {table_name};']
            run_sql_scripts(engine=self.mysql_engine, scripts=scripts)
        else:
            if inspect(self.mysql_engine).has_table(table_name):
                if len(delete_columns) >0:
                    script = f'delete from {table_name} where \n'
                    for i in range(len(delete_columns)):
                        if type(delete_values[i]) == list:
                            values_to_delete = tuple(set(delete_values[i]))
                        else:
                            values_to_delete = f'"{delete_values[i]}"'
                        if i == 0:
                            script += f'{delete_columns[i]} {delete_operators[i]} {values_to_delete} \n'
                        else:
                            script += f'{delete_settings[i-1]} {delete_columns[i]} {delete_operators[i]} {values_to_delete} \n'
                    scripts = [script]
                    run_sql_scripts(engine=self.mysql_engine, scripts=scripts)

        sql_types = Get_SQL_Types(dataframe).data_types
        Change_Sql_Column_Types(engine=self.mysql_engine, Project_name=self.project_name, Table_Name=table_name, DataTypes=sql_types, DataFrame=dataframe)
        Add_Sql_Missing_Columns( engine=self.mysql_engine, Project_name=self.project_name, Table_Name=table_name, DataFrame=dataframe)
        dataframe.to_sql(name=table_name, con=self.mysql_engine, if_exists='append', index=False, schema=self.project_name,
                  chunksize=1000, dtype=sql_types)

        print_color(f'Data For {data_type} imported to {table_name}', color='g')

