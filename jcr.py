import os
from os.path import join, exists

import pandas as pd


def clean_csv_from_jcr(folder: str):
    # Take off the first line which has the system call and params

    _, _, filenames = next(os.walk(folder), (None, None, []))
    print(filenames)
    output_folder = join(folder, 'output')
    if not exists(output_folder):
        os.makedirs(output_folder)
    for file_name in filenames:
        with open(join(folder, file_name), 'r')as f_in:
            lines = f_in.readlines()
            del lines[0:1]
            del lines[-2:]
            with open(join(output_folder, file_name), mode='w+') as f_out:
                f_out.writelines(lines)


def merge_csv(path: str):
    _, _, filenames = next(os.walk(path), (None, None, []))
    filenames = [join(path, f) for f in filenames if str.endswith(f, '.csv')]
    print(filenames)
    result_obj = pd.concat([pd.read_csv(file) for file in filenames])
    # Convert the above object into a csv file and export
    result_obj.drop(columns=['Rank', 'Eigenfactor Score'], inplace=True)
    result_obj.drop_duplicates("Full Journal Title", inplace=True)
    result_obj.to_csv(join(path, 'consolidated.csv'), index=False, encoding="utf-8")


def read_jcr(output_folder: str):
    df = pd.read_csv(join(output_folder, 'consolidated.csv'))
    print(df.head(20))
    # print(df.duplicated())


def clean_consolidated_csv(output_folder: str):
    pass


if __name__ == '__main__':
    input_folder = '/home/lauro/Documents/ana/doutorado/jcr'
    output_folder = join(input_folder, 'output')
    # Limpa as linhas desnecessarias que o JCR adiciona ao CSV
    # clean_csv_from_jcr(input_folder)
    # merge_csv(output_folder)
    read_jcr(output_folder)
