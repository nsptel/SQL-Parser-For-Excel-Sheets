import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from ctypes import windll
from tkinter.ttk import Style
from executer import SQLExecuter, ExecuteError
from datastore.create import create_xml
from xlrd import open_workbook
from os import listdir
from os.path import abspath, join

LARGE_FONT = ('Courier New', 14)
NORM_BOLD_FONT = ('Verdana', 12, 'bold')
SMALL_FONT = ('Verdana', 11)
FILE_PATH = ''
FOLDER_PATH = ''
BOOKS = {}
FINAL_RESULT = None


class SqlApp(tk.Frame):

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)
        windll.shcore.SetProcessDpiAwareness(1)

        MainPage(parent).pack(fill=tk.BOTH, expand=True)
        parent.mainloop()


def get_data(data):
    global BOOKS
    selected_cols = []
    selected_rows = []
    final_result = []
    col_names = []

    for name, path in data[1]:
        book = open_workbook(path)
        BOOKS[name] = book

    if not isinstance(data[0][2], tuple):
        book = BOOKS[data[0][2]]
        sheet = book.sheet_by_name(data[0][2])
        if data[0][0] is not None:
            selected_rows.extend(data[0][0])
        else:
            selected_rows.extend([i for i in range(sheet.nrows)])
        for i in range(sheet.ncols):
            if sheet.cell_value(0, i) in data[0][1]:
                selected_cols.append(i)

        col_names.extend([sheet.cell_value(0, i) for i in selected_cols])

        for i in selected_rows:
            current_row = []
            for j in selected_cols:
                current_row.append(sheet.cell_value(i, j))
            final_result.append(current_row)
    else:
        book1 = BOOKS[data[0][2][0]]
        book2 = BOOKS[data[0][2][1]]
        sheet1 = book1.sheet_by_name(data[0][2][0])
        sheet2 = book2.sheet_by_name(data[0][2][1])

        selected_rows.extend(data[0][0])
        col1_index = []
        col2_index = []

        for i in range(sheet1.ncols):
            if sheet1.cell_value(0, i) in data[0][1][0]:
                col1_index.append(i)
        for i in range(sheet2.ncols):
            if sheet2.cell_value(0, i) in data[0][1][1]:
                col2_index.append(i)

        selected_cols.extend([tuple(col1_index), tuple(col2_index)])

        first_row = [data[0][2][0] + '.' + sheet1.cell_value(0, i) for i in col1_index] + \
                    [data[0][2][1] + '.' + sheet2.cell_value(0, i) for i in col2_index]
        col_names.extend(first_row)
        final_result.append(first_row)

        for i, j in selected_rows:
            current_row = []
            if i is None:
                for _ in selected_cols[0]:
                    current_row.append('null')
            else:
                for x in selected_cols[0]:
                    current_row.append(sheet1.cell_value(i, x))
            if j is None:
                for _ in selected_cols[1]:
                    current_row.append('null')
            else:
                for x in selected_cols[1]:
                    current_row.append(sheet2.cell_value(j, x))
            final_result.append(current_row)

    if len(final_result) == 0:
        final_result.append(col_names)
    return final_result


def open_file(obj):
    global FILE_PATH, FOLDER_PATH

    try:
        FILE_PATH = filedialog.askopenfilenames(filetypes=(('Excel Files (*.xls, *.xlsx)', '*.xls'),
                                                           ('Excel Files (*.xls, *.xlsx)', '*.xlsx')))
    except FileNotFoundError:
        return

    if FOLDER_PATH:
        ans = messagebox.askquestion('Select File',
                                     'You have already selected a folder. If you want to select file instead of the '
                                     'folder than click yes.', icon='warning')
        if ans == 'yes':
            FOLDER_PATH = ''
        else:
            return

    if FILE_PATH:
        obj.config(state=tk.NORMAL)


def open_folder(obj):
    global FILE_PATH, FOLDER_PATH
    try:
        FOLDER_PATH = filedialog.askdirectory()
    except FileNotFoundError:
        FOLDER_PATH = ''
        return

    if FILE_PATH:
        ans = messagebox.askquestion('Select Folder',
                                     'You have already selected a file. If you want to select folder instead of the '
                                     'file than click yes(The file needs to be in the selected folder '
                                     'if you need both).', icon='warning')
        if ans == 'yes':
            FILE_PATH = ''
        else:
            return

    if FOLDER_PATH:
        obj.config(state=tk.NORMAL)
        FILE_PATH = []
        for filename in listdir(FOLDER_PATH):
            if filename.endswith('.xls') or filename.endswith('.xlsx'):
                FILE_PATH.append(abspath(join(FOLDER_PATH, filename)))
        FILE_PATH = tuple(FILE_PATH)


def reset_box(obj):
    obj.delete(1.0, tk.END)


def run_query(queries, controller):
    global FILE_PATH, FINAL_RESULT
    final_result = {}
    metadata = {}
    for file in FILE_PATH:
        metadata[file] = create_xml(file)
    for query in queries.split(';'):
        if query.strip() == '':
            break
        try:
            data_obj = SQLExecuter(query, metadata)
            data = data_obj.return_result()
            if isinstance(data[0], tuple):
                final_result[query] = get_data(data)
            else:
                final_result[query] = data[0]
        except ExecuteError as e:
            final_result[query] = str(e)

    FINAL_RESULT = final_result

    res_app = ShowResult(controller)
    res_app.wm_title('Query Results')
    width = res_app.winfo_screenwidth() - 20
    height = res_app.winfo_screenheight() - 20
    res_app.geometry(f'{width}x{height}+10+10')


def do():
    print('No')


class MainPage(tk.Frame):

    def __init__(self, parent, *args, **kwargs):
        tk.Frame.__init__(self, parent, *args, **kwargs)

        selection = ttk.Frame(self)
        selection.grid(row=0, column=0, sticky=tk.NSEW)

        instructions = ttk.Label(selection,
                                 text='Select file or folder(containing one or more Excel Files) '
                                      'on which you want to perform operations.',
                                 font=SMALL_FONT)
        instructions.grid(row=0, columnspan=2, padx=10, pady=5)

        open_file_btn = ttk.Button(selection, text='Choose File', style='def.TButton',
                                   command=lambda: open_file(query_box))
        open_file_btn.grid(row=1, sticky=tk.W, padx=10, pady=10)

        open_folder_btn = ttk.Button(selection, text='Choose Folder', style='def.TButton',
                                     command=lambda: open_folder(query_box))
        open_folder_btn.grid(row=1, column=1, sticky=tk.W, padx=10, pady=10)

        lbl1 = ttk.Label(self, text='Enter your query below. If multiple, then separate with semi-colon(;).',
                         font=SMALL_FONT)
        lbl1.grid(row=1, sticky=tk.W, padx=10, pady=5)

        query_box = tk.Text(self, width=72, height=12, state=tk.DISABLED, font=LARGE_FONT)
        query_box.grid(row=2, columnspan=2, pady=10, padx=10, sticky=tk.NSEW)

        scrollbar_y = ttk.Scrollbar(self, orient=tk.VERTICAL, command=query_box.yview)
        scrollbar_y.grid(row=2, column=2, sticky=tk.NS)
        query_box['yscrollcommand'] = scrollbar_y.set

        s = Style()
        s.configure('def.TButton', font=SMALL_FONT)

        run_button = ttk.Button(self, text='Run Query', style='def.TButton',
                                command=lambda: run_query(query_box.get(1.0, tk.END), parent))
        run_button.grid(row=3, columnspan=2, sticky=tk.W, pady=5, padx=10)

        reset_btn = ttk.Button(self, text='Reset', style='def.TButton', command=lambda: reset_box(query_box))
        reset_btn.grid(row=3, column=1, sticky=tk.E, pady=5, padx=10)


class ShowResult(tk.Toplevel):

    def __init__(self, parent, *args, **kwargs):
        tk.Toplevel.__init__(self, parent, *args, **kwargs)

        canvas = tk.Canvas(self)
        canvas.pack(fill=tk.BOTH, expand=True)

        yscroll = ttk.Scrollbar(parent, orient=tk.VERTICAL)
        yscroll.pack(side=tk.RIGHT, fill=tk.Y)

        if FINAL_RESULT is not None:
            for query, result in FINAL_RESULT.items():
                label_query = ttk.Label(canvas, text='>>> ' + query, font=SMALL_FONT)
                label_query.pack(pady=10, padx=10, anchor=tk.SW)

                if isinstance(result, list):
                    table = ttk.Treeview(canvas, columns=tuple(result[0]), show='headings')

                    yscrolltable = ttk.Scrollbar(table, orient=tk.VERTICAL)
                    yscrolltable.pack(side=tk.RIGHT, fill=tk.Y)
                    xscrolltable = ttk.Scrollbar(table, orient=tk.HORIZONTAL)
                    xscrolltable.pack(side=tk.BOTTOM, fill=tk.X)

                    for col in result[0]:
                        table.heading(col, text=col)
                    for row in result[1:]:
                        table.insert('', 'end', values=tuple(row))
                    table.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)

                    yscrolltable.config(command=table.yview)
                    xscrolltable.config(command=table.xview)
                    table.configure(xscrollcommand=xscrolltable.set, yscrollcommand=yscrolltable.set)
                else:
                    lbl = ttk.Label(canvas, text=result, font=NORM_BOLD_FONT)
                    lbl.pack(pady=10, padx=10, side=tk.TOP, anchor=tk.W)
                    lbl.configure(foreground='red')

        yscroll.config(command=canvas.yview)
        canvas.configure(yscrollcommand=yscroll.set)


if __name__ == '__main__':
    root = tk.Tk()
    root.resizable(False, False)
    root.title('SQL Query Executer for Excel Sheets')
    app = SqlApp(root)
    root.mainloop()
