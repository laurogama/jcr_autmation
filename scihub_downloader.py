import os
import shutil
from os.path import join, exists
from shutil import copy2

import pandas as pd
import pdfx


def download_links_from_file(doi):
    folder = join(os.path.dirname(doi), 'downloaded')
    if not exists(folder):
        os.makedirs(folder)
    os.chdir(folder)
    with open(doi, mode='r') as doi_links:
        lines = doi_links.readlines()
        for line in lines:
            print('https://sci-hub.do/{}'.format(line))
            os.system("wget -rHA '*.pdf' -e robots=off {}{}".format('https://sci-hub.do/', line))


def download_links_from_list(output_folder, doi_list):
    folder = join(output_folder, 'downloaded/temp')
    if not exists(folder):
        os.makedirs(folder)
    os.chdir(folder)
    for line in doi_list:
        print('https://sci-hub.do/{}'.format(line))
        os.system("wget -rHA '*.pdf' -e robots=off {}{}".format('https://sci-hub.do/', line))


def compare_lists_csv(input_folder):
    main_list = pd.read_csv(join(input_folder, 'outliers_download.csv'))
    zot_list = pd.read_csv(join(input_folder, 'zot_list.csv'))
    # print(main_list.shape)
    # print(zot_list.shape)
    # print(zot_list['DOI'].head())
    # print(main_list.columns)
    DOI = set(main_list.DI)
    downloaded = set(zot_list.DOI)
    print(len(DOI))
    print(len(downloaded))
    result = list(DOI - downloaded)
    print(result)
    print(len(result))
    return result


def compare_lists_excel(input_folder):
    main_list = pd.read_excel(
        join(input_folder, 'outliers.xlsx'),
        engine='openpyxl',
    )
    zot_list = pd.read_csv(join(input_folder, 'zot_list.csv'))
    # print(main_list.shape)
    # print(zot_list.shape)
    # print(zot_list['DOI'].head())
    # print(main_list.columns)
    DOI = set(main_list.DI)
    downloaded = set(zot_list.DOI)
    print(len(DOI))
    print(len(downloaded))
    result = list(DOI - downloaded)
    print(result)
    print(len(result))
    return result


def extract_metadata(filename):
    pdf = pdfx.PDFx(filename)
    # print(pdf.get_metadata())
    try:
        doi = pdf.get_metadata()['dc']['identifier']
        print(doi)
        return doi
    except KeyError:
        print("Filename {} has no DOI")
        return None
    # print(pdf.get_metadata()['Keywords'])


def copy_from_zotero(input_folder):
    main_list = pd.read_excel(
        join(input_folder, 'outliers.xlsx'),
        engine='openpyxl',
    )
    zot_list = pd.read_csv(join(input_folder, 'zot_list.csv'))
    main_list.rename(columns={"DI": "DOI"}, inplace=True)

    output_folder = join(input_folder, 'new_sample')
    main_list['found'] = main_list.DOI.isin(zot_list.DOI)
    # main_list.to_excel(join(input_folder, 'matches.xlsx'))
    # print(main_list['found'])
    for index, row in main_list.iterrows():
        if row.found:
            # print(zot_list.DOI == row.DI)
            match = zot_list.loc[zot_list.DOI == row.DOI]
            filename = match.iloc[0]['File Attachments'].split(';')[0]
            shutil.copy2(filename, output_folder)


def copy_from_files(input_folder):
    main_list = pd.read_excel(
        join(input_folder, 'outliers.xlsx'),
        engine='openpyxl',
    )
    zot_list = pd.read_csv(join(input_folder, 'zot_list.csv'))

    output_folder = join(input_folder, 'new_sample')
    _, _, filenames = next(os.walk(join(input_folder, 'downloaded')), (None, None, []))
    filenames = [join(input_folder, 'downloaded', f) for f in filenames if str.endswith(f, '.pdf')]
    print(filenames)
    for file in filenames:
        doi = extract_metadata(file)
        if doi in main_list.DI:
            copy2(file, join(output_folder, output_folder))


if __name__ == '__main__':
    input_folder = '/home/lauro/Documents/ana/doutorado/jcr3/outliers'
    # Limpa as linhas desnecessarias que o JCR adiciona ao CSV
    # doi = join(input_folder, 'doi.txt')
    # # download_links(doi)
    # diff_list = compare_lists_csv(input_folder)
    # diff_list = compare_lists_excel(input_folder)
    copy_from_zotero(input_folder)
    # download_links_from_list(input_folder, diff_list)
    # filename = '/home/lauro/Documents/ana/doutorado/jcr3/outliers/downloaded/temp/pazienza2020.pdf'
    # extract_metadata(filename)
