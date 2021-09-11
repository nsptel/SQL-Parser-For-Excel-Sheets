from sqlparser.lexer import SQLLexer
from sly import Parser


class SQLParser(Parser):
    # importing tokens from lexer
    tokens = SQLLexer.tokens

    precedence = (
        ('left', OR),
        ('left', AND),
        ('nonassoc', '(', ')')
    )

    # empty string
    @_('')
    def statement(self, p):
        pass

    # root, main query
    @_('"(" statement ")"')
    def statement(self, p):
        pass

    @_('SELECT columns FROM tables')
    def statement(self, p):
        return 'simple_select', p.columns, p.tables

    @_('SELECT columns FROM tables WHERE condition')
    def statement(self, p):
        return 'select_with_cond', ('simple_select', p.columns, p.tables), p.condition

    @_('SELECT columns FROM tables order_grp')
    def statement(self, p):
        return 'simple_select', p.columns, p.tables, p.order_grp

    @_('SELECT columns FROM tables WHERE condition order_grp')
    def statement(self, p):
        return 'select_with_cond', ('simple_select', p.columns, p.tables), p.condition, p.order_grp

    # columns
    @_('identifier "," columns')
    def columns(self, p):
        return [p.identifier] + p.columns

    @_('identifier')
    def columns(self, p):
        return [p.identifier]

    @_('"*"')
    def columns(self, p):
        return '*'

    # tables
    @_('identifier normal_join identifier ON join_cond')
    def tables(self, p):
        return p.normal_join, (p.identifier0, p.identifier1), p.join_cond

    @_('identifier normal_join identifier WHERE join_cond')
    def tables(self, p):
        return p.normal_join, (p.identifier0, p.identifier1), p.join_cond

    @_('identifier normal_natural_join identifier')
    def tables(self, p):
        return p.normal_natural_join, (p.identifier0, p.identifier1), None

    @_('identifier normal_natural_join identifier USING identifier')
    def tables(self, p):
        return p.normal_natural_join, (p.identifier0, p.identifier1), p.identifier2

    @_('identifier')
    def tables(self, p):
        return p.identifier

    # normal natural joins
    @_('NATURAL normal_join')
    def normal_natural_join(self, p):
        result = 'natural_' + p.normal_join
        return result

    @_('NATURAL JOIN')
    def normal_natural_join(self, p):
        return 'natural_join'

    @_('CROSS JOIN')
    def normal_natural_join(self, p):
        return 'cross_join'

    @_('","')
    def normal_natural_join(self, p):
        return 'cross_join'

    # normal joins
    @_('LEFT JOIN')
    def normal_join(self, p):
        return 'left_join'

    @_('LEFT OUTER JOIN')
    def normal_join(self, p):
        return 'left_join'

    @_('RIGHT JOIN')
    def normal_join(self, p):
        return 'right_join'

    @_('RIGHT OUTER JOIN')
    def normal_join(self, p):
        return 'right_join'

    @_('JOIN')
    def normal_join(self, p):
        return 'inner_join'

    @_('INNER JOIN')
    def normal_join(self, p):
        return 'inner_join'

    @_('EQUI JOIN')
    def normal_join(self, p):
        return 'inner_join'

    @_('FULL OUTER JOIN')
    def normal_join(self, p):
        return 'full_outer_join'

    # condition
    @_('condition AND condition')
    def condition(self, p):
        return 'AND', p.condition0, p.condition1

    @_('condition OR condition')
    def condition(self, p):
        return 'OR', p.condition0, p.condition1

    @_('"(" condition ")"')
    def condition(self, p):
        return '(', p.condition, ')'

    @_('identifier GREQ literal')
    def condition(self, p):
        return '>=', p.identifier, p.literal

    @_('identifier LEEQ literal')
    def condition(self, p):
        return '<=', p.identifier, p.literal

    @_('identifier EQ literal')
    def condition(self, p):
        return '==', p.identifier, p.literal

    @_('identifier EQEQ literal')
    def condition(self, p):
        return '==', p.identifier, p.literal

    @_('identifier LEGR literal')
    def condition(self, p):
        return '!=', p.identifier, p.literal

    @_('identifier NTEQ literal')
    def condition(self, p):
        return '!=', p.identifier, p.literal

    @_('identifier "=" literal')
    def condition(self, p):
        return '=', p.identifier, p.literal

    @_('identifier "<" literal')
    def condition(self, p):
        return '<', p.identifier, p.literal

    @_('identifier ">" literal')
    def condition(self, p):
        return '>', p.identifier, p.literal

    @_('identifier LIKE literal')
    def condition(self, p):
        return 'LIKE', p.identifier, p.literal

    @_('identifier BETWEEN literal AND literal')
    def condition(self, p):
        return 'BETWEEN', p.identifier, p.literal0, p.literal1

    # order by and group by
    @_('group_by order_by')
    def order_grp(self, p):
        return p.group_by, p.order_by

    @_('group_by')
    def order_grp(self, p):
        return p.group_by, None

    @_('order_by')
    def order_grp(self, p):
        return None, p.order_by

    @_('ORDER BY identifier')
    def order_by(self, p):
        return 'order_by', 'asc', p.identifier

    @_('ORDER BY identifier ASC')
    def order_by(self, p):
        return 'order_by', 'asc', p.identifier

    @_('ORDER BY identifier DESC')
    def order_by(self, p):
        return 'order_by', 'desc', p.identifier

    @_('GROUP BY columns')
    def group_by(self, p):
        # if p.columns == '*':
        #     pass
        return 'group_by', p.columns, None

    @_('GROUP BY columns HAVING condition')
    def group_by(self, p):
        return 'group_by', p.columns, p.condition

    # any identifier
    @_('IDENTIFIER')
    def identifier(self, p):
        return p.IDENTIFIER

    @_('QUOTED_IDENTIFIER')
    def identifier(self, p):
        return p.QUOTED_IDENTIFIER[1:-1]

    @_('BACKQUOTED_IDENTIFIER')
    def identifier(self, p):
        return p.BACKQUOTED_IDENTIFIER[1:-1]

    # join conditions
    @_('identifier EQ identifier')
    def join_cond(self, p):
        return 'join_cond', p.identifier0, p.identifier1

    # literals, i.e., strings, ints, floats
    @_('STRING')
    def literal(self, p):
        return 'string', p.STRING[1:-1]

    @_('NUMBER')
    def literal(self, p):
        return 'number', p.NUMBER


if __name__ == '__main__':
    lexer = SQLLexer()
    parser = SQLParser()
    while True:
        try:
            string = input('>> ')
        except EOFError:
            break
        except KeyboardInterrupt:
            break
        if string:
            print(parser.parse(lexer.tokenize(string)))
