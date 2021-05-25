import os
from datetime import datetime
from os.path import join, exists

import matplotlib.pyplot as plt
import numpy
import numpy as np
import pandas as pd
import seaborn as sns
from pandas import DataFrame

plt.style.use('seaborn')


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
    result_obj.drop(columns=['Rank', 'Eigenfactor Score', 'Total Cites'], inplace=True)
    result_obj.drop_duplicates("Full Journal Title", inplace=True)
    result_obj['Journal Impact Factor'] = result_obj['Journal Impact Factor'].replace("Not Available", 0)
    result_obj['Journal Impact Factor'] = result_obj['Journal Impact Factor'].replace(numpy.nan, 0)
    result_obj.to_csv(join(path, 'consolidated.csv'), index=False, encoding="utf-8")


def read_jcr(output_folder: str):
    df = pd.read_csv(join(output_folder, 'consolidated.csv'), na_values=["Not Available"])
    print(df.head(10))
    print(df.shape)
    # Removes missing impact factor


def merge_jif(jcr_file: str, bibliometry_file):
    jcr = pd.read_csv(jcr_file, na_values=["Not Available"])
    bib = pd.read_excel(
        bibliometry_file,
        engine='openpyxl',
    )
    bib.astype({'PY': 'int32'})
    bib['SO'] = bib['SO'].str.upper()
    bib['SO'] = bib['SO'].str.replace('\\&', '&')
    jcr["Full Journal Title"] = jcr["Full Journal Title"].str.upper()
    jcr["Full Journal Title"] = jcr["Full Journal Title"].str.replace('\\&', '&')
    # print(bib['SO'])
    # print(jcr['Full Journal Title'])
    merged = pd.merge(bib, jcr, left_on='SO', right_on='Full Journal Title', how='left', validate='many_to_one')
    merged['Journal Impact Factor'] = merged['Journal Impact Factor'].replace(numpy.nan, 0)
    save_output_excel(jcr_file, merged)


def save_output_excel(jcr_file, merged: DataFrame):
    merged_file = join(os.path.dirname(jcr_file), "output.xlsx")
    print("Saving to {}".format(merged_file))
    merged.to_excel(merged_file)
    # select rows with jif equals zero
    jif_not_found = merged[merged['Journal Impact Factor'] == 0]
    jif_not_found = jif_not_found['SO']
    # remove duplicated journals
    jif_not_found = jif_not_found.drop_duplicates(inplace=False)
    jif_not_found_file = join(os.path.dirname(jcr_file), "output_not_found.xlsx")
    print("Saving not found JIF to {}".format(jif_not_found_file))
    jif_not_found.to_excel(jif_not_found_file)


def calculate_outliers(filepath: str):
    df = pd.read_excel(
        filepath,
        engine='openpyxl',
    )
    fic = calc_fixed_impact_factor(df)
    # box plot of the variable height
    ax = sns.boxplot(y=fic['fic'])

    q1 = fic['fic'].quantile(0.25)
    q3 = fic['fic'].quantile(0.75)
    iqr = q3 - q1

    lower_bound = q1 - (1.5 * iqr)
    upper_bound = q3 + (1.5 * iqr)

    print("q1 = {}".format(q1))
    print("q3 = {}".format(q3))
    print("iqr = {}".format(iqr))
    print("upper bound = {}".format(upper_bound))

    # notation indicating an outlier
    fic1 = fic['fic']
    fic1.to_excel(join(os.path.dirname(filepath), "fic.xlsx"))
    outliers = fic[fic['fic'] >= upper_bound]
    outliers.to_excel(join(os.path.dirname(filepath), "outliers.xlsx"))
    count_outlier = 0
    for index, row in fic.iterrows():
        if row['fic'] >= upper_bound:
            count_outlier = count_outlier + 1
            # print(row['TI'])
            # print("Article:{} is outlier with {}".format(row['TI'], row['fic']))
            # ax.annotate(row['TI'], xy=(0, row['fic']), xytext=(0.05, row['fic']), fontsize=12,
            #             arrowprops=dict(arrowstyle='->', ec='grey', lw=2), bbox=dict(boxstyle="round", fc="0.8"))

    # xtick, label, and title
    plt.xticks(fontsize=14)
    plt.xlabel('Mean per year', fontsize=14)
    plt.ylabel('Article Impact Factor', fontsize=14)
    plt.title('Outliers', fontsize=20)
    plt.show()
    print("Outliers Found: {}".format(count_outlier))


def calc_fixed_impact_factor(df):
    df['years_published'] = datetime.today().year - df['PY']
    df['years_published'][df['years_published'] < 1] = 1
    df['median citations'] = df['TC'] / df['years_published']
    df['fic'] = df['median citations'] * (1 + df['Journal Impact Factor'])
    # print(df['fic'])
    return df


def merge_previous_jcr(jcr_antigo, jcr):
    df_jcr = pd.read_excel(jcr,
                           engine='openpyxl',
                           )
    df_jcr_antigo = pd.read_excel(
        jcr_antigo,
        engine='openpyxl',
    )
    df_new = df_jcr_antigo[['SO', 'JCR']].copy()
    df_new.drop_duplicates('SO', inplace=True)
    print(df_jcr.columns)
    merged = pd.merge(df_jcr, df_new, left_on='SO', right_on='SO', how='left', validate='many_to_one')
    merged['Journal Impact Factor'] = merged['Journal Impact Factor'].replace({0: np.nan})
    merged['Journal Impact Factor'] = merged['Journal Impact Factor'].fillna(merged['JCR'])
    print(merged['Journal Impact Factor'])
    merged['Journal Impact Factor'].replace(numpy.nan, 0, inplace=True)
    merged.drop(columns=['JCR'], inplace=True)
    not_found = merged[['SO', 'Journal Impact Factor']].copy()
    not_found = not_found[not_found['Journal Impact Factor'] == 0]
    not_found.drop_duplicates('SO', inplace=True)
    not_found.to_excel(join(os.path.dirname(jcr), "not_found1.xlsx"))
    merged.to_excel(join(os.path.dirname(jcr), "output.xlsx"))
    # save_output_excel(jcr, merged)


def merge_manual_filled(jcr_antigo, jcr):
    df_jcr = pd.read_excel(jcr,
                           engine='openpyxl',
                           )
    df_jcr_antigo = pd.read_excel(
        jcr_antigo,
        engine='openpyxl',
    )
    merged = pd.merge(df_jcr, df_jcr_antigo, left_on='SO', right_on='SO', how='left', validate='many_to_one')
    merged['Journal Impact Factor'].replace(0, numpy.nan, inplace=True)
    merged['Journal Impact Factor'] = merged['Journal Impact Factor'].fillna(merged['JCR'])
    merged.drop(columns=['JCR'], inplace=True)
    merged['Journal Impact Factor'].replace(numpy.nan, 0, inplace=True)
    not_found = merged[['SO', 'Journal Impact Factor']].copy()
    not_found = not_found[not_found['Journal Impact Factor'] == 0]
    not_found.drop_duplicates('SO', inplace=True)

    not_found.to_excel(join(os.path.dirname(jcr), "not_found2.xlsx"))
    merged.to_excel(join(os.path.dirname(jcr), "output2.xlsx"))


def fill_manual_jif(input_file):
    input_folder = '/home/lauro/Documents/ana/doutorado/jcr'
    output_folder = join(input_folder, 'output')
    jcr = join(output_folder, 'output.xlsx')
    # bibliometry = join(output_folder, 'output.xlsx')
    # merge_previous_jcr(join(output_folder, 'jcr_ana.xlsx'), jcr)
    merge_manual_filled(join(output_folder, 'not_found_manual.xlsx'), join(output_folder, 'output.xlsx'))
    # merge_jif(jcr_file=jcr, bibliometry_file=bibliometry)


def drop_2021_documents(df_biblio) -> DataFrame:
    index_names = df_biblio[df_biblio['PY'] == 2021].index
    # drop these row indexes from dataFrame
    df_biblio.drop(index_names, inplace=True)
    return df_biblio


def clean_input_data(biblio_filepath: str) -> DataFrame:
    df_biblio = pd.read_excel(biblio_filepath,
                              engine='openpyxl', )
    df_biblio = drop_2021_documents(df_biblio)
    return df_biblio


if __name__ == '__main__':
    input_folder = '/home/lauro/Documents/ana/doutorado/jcr3'
    # Limpa as linhas desnecessarias que o JCR adiciona ao CSV
    jcr = join(input_folder, 'consolidated.csv')
    bibliometry = join(input_folder, 'amostra_final.xlsx')
    # df = clean_input_data(bibliometry)
    # df.to_excel(bibliometry, index=False)
    # merge_jif(jcr, bibliometry)
    # fill_manual_jif(output_folder)
    calculate_outliers(join(input_folder, 'output.xlsx'))
