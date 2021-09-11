from pathlib import Path
from os.path import abspath, dirname
from ntpath import basename
import hashlib

BUF_SIZE = 65536


def create_xml(file_path):
    global BUF_SIZE
    md5 = hashlib.md5()

    with open(file_path, 'rb') as f:
        while True:
            data = f.read(BUF_SIZE)
            if not data:
                break
            md5.update(data)

    xml_name = r'{md5}.xml'.format(md5=md5.hexdigest())

    file = Path(dirname(dirname(__file__)) + '\\databases\\' + xml_name)

    if file.is_file():
        return abspath(file)
    else:
        with open(abspath(file), 'wb') as f:
            import xml.etree.ElementTree as Et
            from xlrd import open_workbook

            book = open_workbook(file_path)
            sheet_names = book.sheet_names()
            file_name = basename(file_path).split('.')
            file_name = ''.join(file_name[:-1])

            data = Et.Element(file_name)
            sheets = Et.SubElement(data, 'sheets')
            for sheet in sheet_names:
                sheet_temp = Et.SubElement(sheets, 'sheet')
                sheet_temp.text = str(sheet)

                sheet_original = book.sheet_by_name(sheet)
                columns_original = [sheet_original.cell_value(0, i) for i in range(sheet_original.ncols) if sheet_original.cell_value(0, i) is not '']
                columns = Et.SubElement(sheet_temp, 'columns')

                for col in columns_original:
                    col_temp = Et.SubElement(columns, 'column')
                    col_temp.text = str(col)

            f.write(Et.tostring(data))

        return abspath(file)


if __name__ == '__main__':
    xml = create_xml(r'C:\Users\Neel Patel\Documents\VS Code\Python\query executer\SampleData.xlsx')
    print(xml)
