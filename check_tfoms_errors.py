import csv
import json
import xml.etree.ElementTree as etree
import os
import sys
import traceback
from datetime import datetime
import webbrowser
import zipfile


__version__ = '0.4.0'


def read_csv(filename, encoding='utf-8', header=False):
    with open(filename, 'r', newline='', encoding=encoding) as f:
        reader = csv.reader(f, delimiter=';')
        if header:
            next(reader)
        return [row for row in reader]


def write_csv(filename, rows, header=None, encoding='utf-8'):
    with open(filename, 'w', newline='', encoding=encoding) as f:
        writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_NONE, quotechar='')
        if header is not None:
            writer.writerow(header)
        writer.writerows(rows)


def load_Q_015_016_022_023():
    q_data = {}
    for q_file in ('Q015.xml', 'Q016.xml', 'Q022.xml', 'Q023.xml'):
        with open(q_file, 'r', newline='', encoding='cp1251') as f:
            tree = etree.ElementTree(etree.fromstring(f.read()))
            root = tree.getroot()
            for zap in root.findall('zap'):
                q_data[zap.find('ID_TEST').text] = zap

    return q_data


def load_l(filename):
    with open(filename, 'r', newline='', encoding='cp1251') as f:
        tree = etree.ElementTree(etree.fromstring(f.read()))
        root = tree.getroot()
        return {zap.find('ID_PAC').text: zap for zap in root.findall('PERS')}


def load_h(filename):
    with open(filename, 'r', newline='', encoding='cp1251') as f:
        tree = etree.ElementTree(etree.fromstring(f.read()))
        root = tree.getroot()
        return {zap.find('PACIENT').find('ID_PAC').text: zap for zap in root.findall('ZAP')}


def load_v(filename, persons, h_data, q_data, out_filename):
    with open(filename, 'r', newline='', encoding='cp1251') as f:
        tree = etree.ElementTree(etree.fromstring(f.read()))
        root = tree.getroot()
        res = []
        for pr in root.findall('PR'):

            # данные из V файла
            oshib = pr.find('OSHIB').text if pr.find('OSHIB') is not None else ''
            im_pol = pr.find('IM_POL').text if pr.find('IM_POL') is not None else ''
            id_pac = pr.find('ID_PAC').text if pr.find('ID_PAC') is not None else ''
            comment = pr.find('COMMENT').text if pr.find('COMMENT') is not None else ''

            if oshib in q_data:
                q_data_comment = q_data[oshib].find('COMMENT').text if q_data[oshib].find('COMMENT') is not None else ''
            else:
                q_data_comment = ''

            out_row = [oshib, im_pol, id_pac, comment, q_data_comment]

            # данные из L файла
            person = persons.get(id_pac)
            if person is not None:
                for t in ('SNILS', 'FAM', 'IM', 'OT', 'DR', 'MR', 'DOCSER', 'DOCNUM', 'DOCDATE', 'DOCORG'):
                    if person.find(t) is not None:
                        out_row.append(person.find(t).text)
                    else:
                        out_row.append('')
            else:
                out_row += ['' for _ in range(10)]

            # данные из H (С, T, D) файла
            zap = h_data.get(id_pac)
            if zap is not None:
                z_sl = zap.find('Z_SL')
                if z_sl is not None:
                    usl_ok_value = z_sl.find('USL_OK').text if z_sl.find('USL_OK') is not None else '-1'
                    usl_ok_comment = {
                        '1': 'стационар круглосуточный',
                        '2': 'дневной стационар',
                        '3': 'амбулаторная помощь и отказы в АРМ Стационаре',
                        '4': 'скорая',
                        '-1': ''
                    }
                    out_row.append(usl_ok_comment.get(usl_ok_value, ''))
                else:
                    out_row.append('')
            else:
                out_row.append('')

            res.append(out_row)

        header = ['Код ошибки', 'Код поля', 'Код пациента', 'Комментарий ошибки',
                  'Комментарий из Q015/16/22/23', 'СНИЛС', 'Фамилия', 'Имя', 'Отчество', 'Дата рождения',
                  'Место рождения', 'Серия документа', 'Номер документа', 'Дата документа', 'Организация документа',
                  'Условия оказания мед. помощи']
        write_csv(out_filename, res, header=header, encoding='cp1251')


def main():

    # пока не используется
    ARC_XMLS_PREFIXES = {
        'HM': ['LM', 'VM'],
        'CM': ['LM', 'VM'],
        'TM': ['LTM', 'VM'],
        'DPM': ['LP', 'VPM'],
        'DVM': ['LV', 'VVM'],
        'DOM': ['LO', 'VOM'],
        'DSM': ['LS', 'VSM'],
        'DUM': ['LU', 'VUM'],
        'DFM': ['LF', 'VFM']
    }

    try:
        out_file_name = 'out_{}.csv'.format(datetime.now().strftime('%Y-%m-%d_%H-%M-%S'))

        for zip_arc in [file for file in next(os.walk('in'))[2] if file.endswith('ZIP') or file.endswith('zip')]:
            with zipfile.ZipFile(os.path.join('in', zip_arc), 'r') as zip_ref:
                print('Распаковка файла {} ...'.format(zip_arc))
                zip_ref.extractall('in')

        print('Идёт обработка ...')

        v_file = [file for file in next(os.walk('in'))[2] if file.startswith('V') and file.endswith(('XML', 'xml'))][0]
        l_file = [file for file in next(os.walk('in'))[2] if file.startswith('L') and file.endswith(('XML', 'xml'))][0]
        h_file = [file for file in next(os.walk('in'))[2] if file.startswith(('H', 'C', 'T', 'D')) and file.endswith(('XML', 'xml'))][0]

        q_data = load_Q_015_016_022_023()
        persons = load_l(os.path.join('in', l_file))
        h_data = load_h(os.path.join('in', h_file))

        load_v(os.path.join('in', v_file), persons, h_data, q_data, os.path.join('out', out_file_name))

        webbrowser.open(os.path.join('out', out_file_name))
        input('Обработано. Для выхода нажмите Enter')

    except Exception as e:
        print(str(e))
        traceback.print_exc()
        input('Ошибки при обработке. Для выхода нажмите Enter')
        raise e


if __name__ == '__main__':
    rc = 1
    try:
        main()
        rc = 0
    except Exception as e:
        traceback.print_exc()
    sys.exit(rc)
