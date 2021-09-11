import xml.etree.ElementTree as Et
from sqlparser.lexer import SQLLexer
from sqlparser.parser import SQLParser
from xlrd import open_workbook
from sly.yacc import GrammarError, YaccError, LALRError
from sys import exit


class ExecuteError(Exception):

    def __init__(self, error):
        super().__init__(error)


class SQLExecuter():

    def __init__(self, query, xml_list):
        lexer = SQLLexer()
        parser = SQLParser()
        self.tree = None
        try:
            self.tree = parser.parse(lexer.tokenize(query))
        except GrammarError as g:
            raise ExecuteError('Error: ' + str(g)[6:])
        except LALRError as l:
            raise ExecuteError('Error: ' + str(l)[6:])
        except YaccError as y:
            raise ExecuteError('Error: ' + str(y)[6:])
        self.is_join_query = False
        self.tables = []
        if self.tree is not None:
            self.tables.extend(self.extract_tables())
        else:
            self.gen_error('Syntax error present in the query.')
        self.metadata = {}
        self.originally_selected = None
        self.first_sheet = None
        self.second_sheet = None

        for excel_file, xml_file in xml_list.items():
            tree = Et.parse(xml_file)
            root = tree.getroot()
            for _ in root:
                for child in _:
                    if child.text in self.tables:
                        self.metadata[excel_file] = xml_file
                        break
        if len(self.metadata) == 0:
            self.gen_error('Query entered does not have any sheets corresponding to the given files.')

        self.books = {}
        self.create_workbooks()
        self.final_result = self.walk_tree(self.tree)

    # Finding Identifiers
    def find_element(self, item):
        items = item.split('.')
        for excel, xml in self.metadata.items():
            temp_tree = Et.parse(xml)
            root = temp_tree.getroot()
            if len(items) == 1:
                for _ in root:
                    for child_sheet in _:
                        if items[0] == child_sheet.text:
                            return excel, child_sheet.text, None
                        for _ in child_sheet:
                            for child_col in _:
                                if items[0] == child_col.text:
                                    return excel, child_sheet.text, child_col.text
            elif len(items) == 2:
                if items[0] == root.tag:
                    for _ in root:
                        for child_sheet in _:
                            if items[1] == child_sheet.text:
                                return excel, child_sheet.text, None
                else:
                    for _ in root:
                        for child_sheet in _:
                            if items[0] == child_sheet.text:
                                for _ in child_sheet:
                                    for child_col in _:
                                        if items[1] == child_col.text:
                                            return excel, child_sheet.text, child_col.text
            elif len(items) == 3:
                if items[0] == root.tag:
                    for _ in root:
                        for child_sheet in _:
                            if items[0] == child_sheet.text:
                                for _ in child_sheet:
                                    for child_col in _:
                                        if items[1] == child_col.text:
                                            return excel, child_sheet.text, child_col.text

    # remove the elements after condition checking
    @staticmethod
    def remove_after_condition(rows, filter1, filter2, first=True, if_and=True):
        being_removed = []
        if filter2 is None:
            if first:
                if if_and:
                    for x, y in rows:
                        if x not in filter1:
                            being_removed.append((x, y))
            else:
                if if_and:
                    for x, y in rows:
                        if y not in filter1:
                            being_removed.append((x, y))
        else:
            if first:
                if if_and:
                    for x, y in rows:
                            if x not in filter1 or y not in filter2:
                                being_removed.append((x, y))
                else:
                    for x, y in rows:
                            if x not in filter1 and y not in filter2:
                                being_removed.append((x, y))
            else:
                if if_and:
                    for y, x in rows:
                        if x not in filter1 or y not in filter2:
                            being_removed.append((x, y))
                else:
                    for y, x in rows:
                        if x not in filter1 and y not in filter2:
                            being_removed.append((x, y))
        return being_removed

    # find column with same name
    @staticmethod
    def find_same_col(sheet1, sheet2, using=None):
        col1 = [sheet1.cell_value(0, index) for index in range(sheet1.ncols) if sheet1.cell_value(0, index) is not '']
        col2 = [sheet2.cell_value(0, index) for index in range(sheet2.ncols) if sheet2.cell_value(0, index) is not '']
        if using is None:
            same = [item for item in col1 if item in item in col2]
            try:
                return same[0]
            except IndexError:
                return 'Given sheets does not have any common elements.'
        else:
            if using in col1 and using in col2:
                return using
            else:
                return 'Error at USING clause. Given sheets does not contain the column.'

    # order by and group by for both with and without conditions
    def order_group_by(self, tree, result_rows):
        if isinstance(tree[3][0], tuple) and isinstance(tree[3][1], tuple):
            # both order by and group by
            pass
        elif tree[3][0] is not None:
            """
            if not self.is_join_query:
                columns = tree[3][1][1]
                col_index = []
                values = []
                if len(columns) >= 1:
                    excel, sheet_name, col = self.find_element(columns[0])
                    if len(columns) > 1:
                        for col in columns[1:]:
                            excel_1, sheet_1, _ = self.find_element(col)
                            if excel_1 != excel or sheet_1 != sheet_name:
                                print('Error at GROUP BY clause. columns does not belong to the same sheet.')
                                exit(0)
                    sheet = open_workbook(excel).sheet_by_name(sheet_name)
                    for i in range(sheet.ncols):
                        if sheet.cell_value(0, i) in columns:
                            col_index.append(i)
                    if result_rows is None:
                        result_rows = [i for i in range(1, sheet.nrows)]
                    for i in result_rows:
                        temp = ''
                        for j in col_index:
                            temp = temp + '.' + str(sheet.cell_value(i, j))
                        values.append(temp)
            """
            pass
        else:
            # order by
            tup = (tree[3][1][0], tree[3][1][1], tree[3][1][2])
            sorted_rows, sheet_name = self.walk_tree(tup)
            if self.is_join_query:
                temp_rows = []
                if sheet_name == self.first_sheet:
                    for i in sorted_rows:
                        for j, _ in result_rows:
                            if i == j:
                                temp_rows.append((j, _))
                elif sheet_name == self.second_sheet:
                    for i in sorted_rows:
                        for _, j in result_rows:
                            if i == j:
                                temp_rows.append((_, j))
                result_rows = temp_rows
            else:
                if result_rows is None:
                    result_rows = sorted_rows
                else:
                    result_rows = [item for item in sorted_rows if item in result_rows]
        return result_rows

    # generate error and return it
    @staticmethod
    def gen_error(string):
        return string

    # recursive function which takes care of extracting the indexes of the data required
    def walk_tree(self, tree):

        # Arithmetic Operators
        if tree[0] == '=' or tree[0] == '==' or tree[0] == '<' or tree[0] == '>' or tree[0] == '!=' or tree[0] == '>=' or tree[0] == '<=':
            if tree[0] == '=':
                tree[0] = '=='
            literal = tree[2]
            if literal[0] == 'number':
                literal = float(literal[1])
            else:
                literal = str(literal[1])
            excel_path, sheet_name, col = self.find_element(tree[1])
            book = self.books[excel_path]
            sheet = book.sheet_by_name(sheet_name)
            result_rows = []
            for col_index in range(sheet.ncols):
                if sheet.cell_value(0, col_index) == col:
                    for row_index in range(1, sheet.nrows):
                        val_current = sheet.cell_value(row_index, col_index)
                        if isinstance(literal, float):
                            val_current = float(val_current)
                        else:
                            val_current = str(val_current)
                        try:
                            if eval('val_current ' + tree[0] + ' literal'):
                                result_rows.append(row_index)
                        except TypeError:
                            return 'Types does not match in the given WHERE clause conditions.'
                    break
            return result_rows, sheet_name

        # Between Clause
        if tree[0] == 'BETWEEN':
            literal0 = str(tree[2][1])
            literal1 = str(tree[3][1])
            excel_path, sheet_name, col = self.find_element(tree[1])
            book = self.books[excel_path]
            sheet = book.sheet_by_name(sheet_name)
            result_rows = []
            for col_index in range(sheet.ncols):
                if sheet.cell_value(0, col_index) == col:
                    for row_index in range(1, sheet.nrows):
                        val_current = str(sheet.cell_value(row_index, col_index))
                        try:
                            if eval('literal0 <= val_current <= literal1'):
                                result_rows.append(row_index)
                        except TypeError:
                            return 'Types does not match in the given WHERE clause conditions.'
                    break
            return result_rows, sheet_name

        # Like Clause
        if tree[0] == 'LIKE':
            from re import match
            regex = '^'
            literal = tree[2][1]
            for ch in literal:
                if ch == '_':
                    regex = regex + r'[a-zA-Z0-9_\s]'
                elif ch == '%':
                    regex = regex + r'[a-zA-Z0-9_\s]*'
                else:
                    regex = regex + ch
            regex = regex + '$'
            excel_path, sheet, col = self.find_element(tree[1])
            book = self.books[excel_path]
            sheet = book.sheet_by_name(sheet)
            result_rows = []
            for col_index in range(sheet.ncols):
                if sheet.cell_value(0, col_index) == col:
                    for row_index in range(1, sheet.nrows):
                        val_current = str(sheet.cell_value(row_index, col_index))
                        if match(regex, val_current):
                            result_rows.append(row_index)
                    break
            return result_rows, sheet

        # AND Clause
        if tree[0] == 'AND':
            result1, sheet1 = self.walk_tree(tree[1])
            result2, sheet2 = self.walk_tree(tree[2])
            if not self.is_join_query:
                result_rows = [item for item in result1 if item in result2]
                return result_rows, None
            else:
                removing = []
                if sheet1 is None or sheet2 is None:
                    if sheet1 is None and sheet2 is None:
                        self.originally_selected = [item for item in result1 if item in result2]
                    elif sheet1 is None:
                        if sheet2 == self.first_sheet:
                            temp_rows = self.remove_after_condition(result1, result2, None, first=False)
                        else:
                            temp_rows = self.remove_after_condition(result1, result2, None)
                        self.originally_selected = [item for item in self.originally_selected if item not in temp_rows]
                        del temp_rows
                    else:
                        if sheet1 == self.first_sheet:
                            temp_rows = self.remove_after_condition(result2, result1, None)
                        else:
                            temp_rows = self.remove_after_condition(result2, result1, None, first=False)
                        self.originally_selected = [item for item in self.originally_selected if item not in temp_rows]
                        del temp_rows
                    return self.originally_selected, None
                elif sheet1 == sheet2:
                    result_rows = [item for item in result1 if item in result2]
                    print(result_rows)
                    if self.first_sheet == sheet1:
                        removing.extend(self.remove_after_condition(self.originally_selected, result_rows, None))
                    else:
                        removing.extend(self.remove_after_condition(self.originally_selected, result_rows, None, first=False))
                else:
                    if sheet1 == self.first_sheet:
                        removing.extend(self.remove_after_condition(self.originally_selected, result1, result2))
                    else:
                        removing.extend(self.remove_after_condition(self.originally_selected, result2, result1, first=False))
                self.originally_selected = [item for item in self.originally_selected if item not in removing]
                return self.originally_selected, None

        # OR Clause
        if tree[0] == 'OR':
            result1, sheet1 = self.walk_tree(tree[1])
            result2, sheet2 = self.walk_tree(tree[2])
            if not self.is_join_query:
                result_rows = []
                for item in result1 + result2:
                    if item not in result_rows:
                        result_rows.append(item)
                return result_rows, None
            else:
                removing = []
                if sheet1 is None or sheet2 is None:
                    if sheet1 is None and sheet2 is None:
                        self.originally_selected = []
                        for item in result1 + result2:
                            if item not in self.originally_selected:
                                self.originally_selected.append(item)
                    elif sheet1 is None:
                        if sheet2 == self.first_sheet:
                            temp_rows = self.remove_after_condition(result1, result2, None, first=False, if_and=False)
                        else:
                            temp_rows = self.remove_after_condition(result2, result1, None, if_and=False)
                        self.originally_selected = [item for item in self.originally_selected if item not in temp_rows]
                        del temp_rows
                    else:
                        if sheet1 == self.first_sheet:
                            temp_rows = self.remove_after_condition(result2, result1, None, if_and=False)
                        else:
                            temp_rows = self.remove_after_condition(result2, result1, None, first=False, if_and=False)
                        self.originally_selected = [item for item in self.originally_selected if item not in temp_rows]
                        del temp_rows
                    return self.originally_selected, None
                elif sheet1 == sheet2:
                    result_rows = []
                    for item in result1 + result2:
                        if item not in result_rows:
                            result_rows.append(item)
                    if self.first_sheet == sheet1:
                        removing.extend(self.remove_after_condition(self.originally_selected, result_rows, None,
                                                                    if_and=False))
                    else:
                        removing.extend(self.remove_after_condition(self.originally_selected, result_rows, None,
                                                                    first=False, if_and=False))
                else:
                    if sheet1 == self.first_sheet:
                        removing.extend(self.remove_after_condition(self.originally_selected, result1, result2,
                                                                    if_and=False))
                    else:
                        removing.extend(self.remove_after_condition(self.originally_selected, result2, result1,
                                                                    first=False, if_and=False))
                self.originally_selected = [item for item in self.originally_selected if item not in removing]
                return self.originally_selected, None

        # ( condition )
        if tree[0] == '(':
            result_rows = self.walk_tree(tree[1])
            return result_rows

        # Simple Select
        if tree[0] == 'simple_select':
            result_cols = []
            result_table = None
            result_rows = None
            # Normal queries
            if not isinstance(tree[2], tuple):
                if tree[1] != '*':
                    for col in tree[1]:
                        result_cols.append(self.find_element(col))
                excel_path, result_table, _ = self.find_element(tree[2])
                is_valid = True
                for col in result_cols:
                    if col[1] != result_table:
                        is_valid = False
                if tree[1] == '*':
                    temp_tree_for_col = Et.parse(self.metadata[excel_path])
                    root = temp_tree_for_col.getroot()
                    for _ in root:
                        for child in _:
                            if child.text == result_table:
                                for _child in child:
                                    for child_col in _child:
                                        result_cols.append(child_col.text)
                if not is_valid:
                    return 'Columns required does not belong to the corresponding given sheets.'
            # Join queries
            else:
                excel_1, table_1, _ = self.find_element(tree[2][1][0])
                excel_2, table_2, _ = self.find_element(tree[2][1][1])
                col_1 = []
                col_2 = []
                is_valid = True
                if tree[1] != '*':
                    for col in tree[1]:
                        temp_excel, temp_table, _ = self.find_element(col)
                        if temp_table == table_1:
                            col_1.append(col.split('.')[-1])
                        elif temp_table == table_2:
                            col_2.append(col.split('.')[-1])
                        else:
                            is_valid = False
                    if not is_valid:
                        return 'Columns required does not belong to the corresponding given sheets.'
                else:
                    sheet1 = self.books[excel_1].sheet_by_name(table_1)
                    sheet2 = self.books[excel_2].sheet_by_name(table_2)

                    for i in range(sheet1.ncols):
                        col_1.append(sheet1.cell_value(0, i))
                    for i in range(sheet2.ncols):
                        col_2.append(sheet2.cell_value(0, i))

                result_cols.extend([tuple(col_1), tuple(col_2)])
                result_table = tuple([table_1, table_2])

                result_rows = self.walk_tree(tree[2])
            """
            # exchanging the column tuple with string
            if isinstance(result_cols[0], tuple):
                for index, col in enumerate(result_cols):
                    result_cols[index] = col[2]
            """
            # ordering and grouping
            if len(tree) == 4:
                result_rows = self.order_group_by(tree, result_rows)

            return result_rows, result_cols, result_table

        # Select statements with conditions
        if tree[0] == 'select_with_cond':
            result_rows, result_cols, result_table = self.walk_tree(tree[1])
            print(result_rows)
            self.originally_selected = result_rows
            if self.is_join_query:
                temp_rows, sheet = self.walk_tree(tree[2])
                if len(temp_rows) > 0:
                    if not isinstance(temp_rows[0], tuple):
                        temp = []
                        if sheet == self.first_sheet:
                            for i, j in result_rows:
                                if i not in temp_rows:
                                    temp.append((i, j))
                        else:
                            for i, j in result_rows:
                                if j not in temp_rows:
                                    temp.append((i, j))
                        self.originally_selected = [item for item in self.originally_selected if item not in temp]
                        del temp
                    else:
                        self.originally_selected = [tup for tup in self.originally_selected if tup in result_rows]
                else:
                    self.originally_selected = []
                return self.originally_selected, result_cols, result_table
            else:
                result_rows, _ = self.walk_tree(tree[2])
            # ordering and grouping
            if len(tree) == 4:
                result_rows = self.order_group_by(tree, result_rows)

            return result_rows, result_cols, result_table

        # common for all JOIN ON clauses
        if tree[0] == 'join_cond':
            excel_1, table_1, col_1 = self.find_element(tree[1])
            excel_2, table_2, col_2 = self.find_element(tree[2])
            sheet_1 = self.books[excel_1].sheet_by_name(table_1)
            sheet_2 = self.books[excel_2].sheet_by_name(table_2)
            self.first_sheet = table_1
            self.second_sheet = table_2

            for i in range(sheet_1.ncols):
                if sheet_1.cell_value(0, i) == col_1:
                    col_1 = i
                    break
            for i in range(sheet_2.ncols):
                if sheet_2.cell_value(0, i) == col_2:
                    col_2 = i
                    break
            inner_rows = []
            remaining1 = [i for i in range(1, sheet_1.nrows)]
            remaining2 = [i for i in range(1, sheet_2.nrows)]
            for row1 in range(1, sheet_1.nrows):
                for row2 in range(1, sheet_2.nrows):
                    if str(sheet_1.cell_value(row1, col_1)) == str(sheet_2.cell_value(row2, col_2)):
                        inner_rows.append((row1, row2))
            for i, j in inner_rows:
                if i in remaining1:
                    remaining1.remove(i)
                if j in remaining2:
                    remaining2.remove(j)

            return inner_rows, remaining1, remaining2

        # left join and left outer join
        if tree[0] == 'left_join':
            result_rows, remaining, _ = self.walk_tree(tree[2])
            for i in remaining:
                result_rows.append((i, None))
            return result_rows

        # right join and right outer join
        if tree[0] == 'right_join':
            result_rows, _, remaining = self.walk_tree(tree[2])
            for i in remaining:
                result_rows.append((None, i))
            return result_rows

        # inner join
        if tree[0] == 'inner_join':
            result_rows, _, _ = self.walk_tree(tree[2])
            return result_rows

        # full outer join
        if tree[0] == 'full_outer_join':
            result_rows, remaining1, remaining2 = self.walk_tree(tree[2])
            for i in remaining1:
                result_rows.append((i, None))
            for i in remaining2:
                result_rows.append((None, i))
            return result_rows

        # natural joins
        if str(tree[0]).startswith('natural_') and str(tree[0]).endswith('_join'):
            excel_file1, sheet1_name, _ = self.find_element(tree[1][0])
            excel_file2, sheet2_name, _ = self.find_element(tree[1][1])
            sheet1 = self.books[excel_file1].sheet_by_name(sheet1_name)
            sheet2 = self.books[excel_file2].sheet_by_name(sheet2_name)

            if tree[2] is not None:
                _, _, col = self.find_element(tree[2])
                common_col = self.find_same_col(sheet1, sheet2, using=col)
            else:
                common_col = self.find_same_col(sheet1, sheet2)

            tup = ('join_cond', sheet1_name + '.' + common_col, sheet2_name + '.' + common_col)

            if tree[0] == 'natural_left_join':
                result_rows, remaining, _ = self.walk_tree(tup)
                for i in remaining:
                    result_rows.append((i, None))
                return result_rows
            elif tree[0] == 'natural_right_join':
                result_rows, _, remaining = self.walk_tree(tup)
                for i in remaining:
                    result_rows.append((None, i))
                return result_rows
            elif tree[0] == 'natural_inner_join':
                result_rows, _, _ = self.walk_tree(tup)
                return result_rows
            elif tree[0] == 'natural_full_outer_join':
                result_rows, remaining1, remaining2 = self.walk_tree(tup)
                for i in remaining1:
                    result_rows.append((i, None))
                for i in remaining2:
                    result_rows.append((None, i))
                return result_rows

            return None

        # cross join
        if tree[0] == 'cross_join':
            excel_1, table_1, col_1 = self.find_element(tree[1][0])
            excel_2, table_2, col_2 = self.find_element(tree[1][1])
            sheet_1 = self.books[excel_1].sheet_by_name(table_1)
            sheet_2 = self.books[excel_2].sheet_by_name(table_2)
            result_rows = []

            for row1 in range(1, sheet_1.nrows):
                for row2 in range(1, sheet_2.nrows):
                    result_rows.append((row1, row2))

            return result_rows

        # order by
        if tree[0] == 'order_by':
            excel_file, sheet_name, col = self.find_element(tree[2])
            sheet = self.books[excel_file].sheet_by_name(sheet_name)
            col_index = None
            for i in range(sheet.ncols):
                if sheet.cell_value(0, i) == col:
                    col_index = i
                    break
            if col_index is not None:
                from operator import itemgetter
                unordered = [(i, sheet.cell_value(i, col_index)) for i in range(1, sheet.nrows)]
                if tree[1] == 'asc':
                    ordered = sorted(unordered, key=itemgetter(1))
                else:
                    ordered = sorted(unordered, key=itemgetter(1), reverse=True)
                ordered = [item[0] for item in ordered]
                return ordered, sheet_name
            else:
                print('Error at order by clause. Could not find specified column.')
                exit(0)

        # group by

    # Creating a list of objects returned by open_workbook method
    def create_workbooks(self):
        for excel_file in self.metadata.keys():
            book = open_workbook(excel_file)
            self.books[excel_file] = book

    # Extracting the table names from the parsed tree structure
    def extract_tables(self):
        tables = []

        def remove_dot(table_name):
            if '.' in table_name:
                table_name = table_name.split('.')[-1]
            return table_name

        try:
            if self.tree[0] == 'simple_select':
                if isinstance(self.tree[2], tuple):
                    self.is_join_query = True
                    for table in self.tree[2][1]:
                        tables.append(remove_dot(table))
                elif isinstance(self.tree[2], str):
                    tables.append(remove_dot(self.tree[2]))
            elif self.tree[1][0] == 'simple_select':
                if isinstance(self.tree[1][2], tuple):
                    self.is_join_query = True
                    for table in self.tree[1][2][1]:
                        tables.append(remove_dot(table))
                elif isinstance(self.tree[1][2], str):
                    tables.append(remove_dot(self.tree[1][2]))
        except TypeError:
            return tables
        return tables

    def return_result(self):
        excel = []
        if isinstance(self.final_result, tuple):
            if isinstance(self.final_result[2], tuple):
                for item in self.final_result[2]:
                    temp_excel, _, _ = self.find_element(item)
                    excel.append((item, temp_excel))
            else:
                temp_excel, _, _ = self.find_element(self.final_result[2])
                excel.append((self.final_result[2], temp_excel))
        return self.final_result, excel

if __name__ == '__main__':
    # select `Sales.Units`, `Sales.Rep`, `Users.Password` from `Sales` natural right join `Users` where `Sales.Units` > 60 or `Users.Password` = 'Nilpatel' or Sales.Region = 'East'
    # select * from Sales left join Users on Sales.Units = Users.Units order by Sales.Units
    sqlexec = SQLExecuter("select from Sales",
                          {r'C:\Users\Neel Patel\Documents\SampleData.xlsx':
                           r'C:\Users\Neel Patel\PycharmProjects\SQLParser\databases\b3d37a4d5953d523c43892c439d048bf.xml'})
