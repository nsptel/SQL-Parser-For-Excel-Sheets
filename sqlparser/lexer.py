from sly import Lexer


class SQLLexer(Lexer):
    # tokens used in sql selection group queries
    tokens = {SELECT, FROM, WHERE, LIKE, ON, AND, OR, USING, LEFT, RIGHT, BETWEEN,
              FULL, OUTER, INNER, NATURAL, EQUI, CROSS, JOIN, GREQ, LEEQ,
              EQ, EQEQ, LEGR, NTEQ, QUOTED_IDENTIFIER, BACKQUOTED_IDENTIFIER,
              IDENTIFIER, STRING, NUMBER, ORDER, GROUP, BY, HAVING, ASC, DESC}
    # ignore these while parsing
    ignore = '\n '
    # one character tokens
    literals = {'*', '>', '<', '.', ',', '(', ')', ';'}

    # defining the tokens
    SELECT = r'(?i)SELECT'
    FROM = r'(?i)FROM'
    WHERE = r'(?i)WHERE'
    BETWEEN = r'(?i)BETWEEN'
    LIKE = r'(?i)LIKE'
    AND = r'(?i)AND'
    ORDER = r'(?i)ORDER'
    GROUP = r'(?i)GROUP'
    BY = r'(?i)BY'
    HAVING = r'(?i)HAVING'
    ASC = r'(?i)ASC'
    DESC = r'(?i)DESC'
    OR = r'(?i)OR'
    ON = r'(?i)ON'
    USING = r'(?i)USING'
    LEFT = r'(?i)LEFT'
    RIGHT = r'(?i)RIGHT'
    FULL = r'(?i)FULL'
    OUTER = r'(?i)OUTER'
    INNER = r'(?i)INNER'
    NATURAL = r'(?i)NATURAL'
    CROSS = r'(?i)CROSS'
    EQUI = r'(?i)EQUI'
    JOIN = r'(?i)JOIN'
    GREQ = r'>='
    LEEQ = r'<='
    EQEQ = r'=='
    EQ = r'='
    LEGR = r'<>'
    NTEQ = r'!='

    @_(r'(\d+\.\d+)|(\d+)')
    def NUMBER(self, t):
        return t

    @_(r'"([^"]|"")*"')
    def QUOTED_IDENTIFIER(self, t):
        return t

    @_(r'`([^`]|``)*`')
    def BACKQUOTED_IDENTIFIER(self, t):
        return t

    @_(r'[a-zA-Z0-9_][a-zA-Z0-9_@:-]*(\.[a-zA-Z0-9_][a-zA-Z0-9_@:-]*)?')
    def IDENTIFIER(self, t):
        return t

    @_(r"'([^']|'')*'")
    def STRING(self, t):
        return t

    def error(self, t):
        print('Invalid Character: token = "' + t.value[0] + '"')

    """
    @_(r'--.*')
    def COMMENT(self, t):
        pass
    """


if __name__ == '__main__':
    lexer = SQLLexer()

    print('type "exit()" to exit from the interactive shell.')
    while True:
        try:
            string = input('>>> ')
        except EOFError:
            break
        except KeyboardInterrupt:
            break
        if string == 'exit()':
            break
        if string:
            lex = lexer.tokenize(string)
            for token in lex:
                print(token)