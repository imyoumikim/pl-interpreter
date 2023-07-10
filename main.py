import sys
import os
from dataclasses import dataclass

# 새로 만든 것들
func_dict = {}  # {"함수명1" : ["실행문1", "실행문2", ...], "함수명2": ["실행문1", "실행문2", ...]}
func_name = ''  # 함수명
executions = []  # 실행문 리스트
var_def_line = ''
ari_stack = []
func_name_stack = []
dn = 0
nums = 0
ra = ''  # return address
has_error = False
this_dynamic_link = 0


@dataclass
class Ari:
    local_variables: list
    dynamic_link: int = None
    return_addr: str = None

    def __getitem__(self, item):
        return getattr(self, item)


next_token = 0  # int. token type을 저장
token_count = [0] * 3
char_class = 0  # int
lexeme = [0] * 50  # char[20]
next_char = 0  # char
lex_len = 0  # int
token_string = ''  # lexical()에서 찾아낸 토큰의 lexeme

data = []  # txt파일의 내용을 한글자씩 잘라서 리스트로 저장
data_idx = 0  # data 리스트 내에서 현재 확인 중인 문자의 인덱스
this_line = ''  # 현재 확인하고 있는 라인
operand_name = ''  # 참조되지 않은 변수명
warning_cnt = 0

# 상수 선언(문자 유형)
LETTER = 0
DIGIT = 1
UNKNOWN = 99
EOF = -1  # EOF
UNDERBAR = 2

# 토큰 코드
INT_LIT = 10
IDENT = 11
ASSIGN_OP = 20
ADD_OP = 21
MULT_OP = 23
LEFT_PAREN = 25
RIGHT_PAREN = 26
SEMICOLON = 27
LEFT_BRACE = 28
RIGHT_BRACE = 29
VAR = 30
CALL = 31
PRINTARI = 32
COMMA = 33


# next_char을 lexeme[]에 추가
def addChar():
    global next_char, lex_len, lexeme

    if (lex_len <= 50):
        lexeme[lex_len] = next_char
        lex_len += 1
        lexeme[lex_len] = 0  # lexeme의 다음 칸은 0으로 채움

    else:
        print("Error - lexeme is too long")


# 입력으로부터 next_char를 가져와서 char_class(그 문자의 타입/유형)을 결정
def getChar():
    global next_char, char_class, data_idx, data

    next_char = data[data_idx]  # 다음 문자를 next_char에 넣기

    if next_char == '$':  # EOF
        char_class = EOF

    elif next_char.isalpha():  # 문자인가?
        char_class = LETTER

    elif next_char.isdigit():  # 숫자인가?
        char_class = DIGIT

    elif next_char == '_':
        char_class = UNDERBAR

    else:
        char_class = UNKNOWN

    data_idx += 1  # 다음 문자로 넘어가기


# 비공백 문자를 반환할 때까지 getChar 호출
def getNonBlank():
    while next_char.isspace():  # '\n', '\t', ' ' 모두 True
        getChar()


# UNKNOWN일 때 연산자와 괄호를 조사하여 그 토큰을 반환
def lookup(ch):
    global next_token

    if ch == '(':
        addChar()
        next_token = LEFT_PAREN

    elif ch == ')':
        addChar()
        next_token = RIGHT_PAREN

    elif ch == '{':
        addChar()
        next_token = LEFT_BRACE

    elif ch == '}':
        addChar()
        next_token = RIGHT_BRACE

    elif ch == ',':
        addChar()
        next_token = COMMA

    elif ch == '+':
        addChar()
        next_token = ADD_OP
        token_count[2] += 1  # token_count[2]는 OP의 개수

    elif ch == '*':
        addChar()
        next_token = MULT_OP
        token_count[2] += 1  # token_count[2]는 OP의 개수

    elif ch == ';':
        addChar()
        next_token = SEMICOLON

    elif ch == ':':
        addChar()
        getChar()
        if next_char == '=':  # : 다음에 =가 아니면 에러
            addChar()
            next_token = ASSIGN_OP

    return next_token


# lexical()은 입력 스트림을 분석하여 하나의 lexeme을 찾아낸 뒤, 그것의 token type을 next_token에 저장하고,
# lexeme 문자열을 token_string에 저장하는 함수
def lexical():
    global next_token, lex_len, char_class, lexeme, token_count, token_string

    lex_len = 0
    getNonBlank()  # 공백이 아닐 때까지 getChar()

    if char_class == LETTER:
        addChar()
        getChar()  # next_char를 가져와서 char_class을 결정
        while char_class == LETTER or char_class == UNDERBAR:
            addChar()
            getChar()

        concat = []
        k = 0
        while lexeme[k] != 0:
            concat.append(lexeme[k])
            k += 1
        concat = ''.join(concat)

        if concat == 'variable':
            next_token = VAR
        elif concat == 'call':
            next_token = CALL
        elif concat == 'print_ari':
            next_token = PRINTARI
        else:
            next_token = IDENT  # 사용자 지정 변수
            token_count[0] += 1  # token_count[0]은 ID의 개수

    elif char_class == DIGIT:
        addChar()
        getChar()
        while char_class == DIGIT:
            addChar()
            getChar()
        next_token = INT_LIT  # 상수
        token_count[1] += 1  # token_count[1]은 CONST의 개수

    elif char_class == UNKNOWN:  # 괄호, 연산자
        lookup(next_char)
        getChar()

    elif char_class == EOF:
        next_token = EOF
        lexeme[0] = 'E'
        lexeme[1] = 'O'
        lexeme[2] = 'F'
        lexeme[3] = 0

    i = 0
    word = []
    while lexeme[i] != 0:
        word.append(lexeme[i])
        i += 1
    token_string = ''.join(word)


def start():  # 프로그램 시작
    getChar()
    lexical()
    functions()


def functions():
    function()
    if next_token == IDENT:  # 함수명이 뒤이어 또 있으면
        functions()


def function():
    global func_name, executions

    func_name = ''  # 함수명 초기화
    executions = []  # 실행문 리스트 초기화

    if next_token == IDENT:  # 현재 함수명
        func_name = token_string
        lexical()
        if next_token == LEFT_BRACE:  # {
            function_body()
            lexical()
            if next_token == RIGHT_BRACE:  # }
                pass

    func_dict[func_name] = executions


# <function_body> -> <var_definitions><statements> | <statements>
def function_body():
    lexical()
    if next_token == VAR:
        var_definitions()

    statements()


# <var_definitions> -> <var_definition> | <var_definition> <var_definitions>
def var_definitions():
    var_definition()
    lexical()
    if next_token == VAR:  # 여기서 VAR가 아니면
        var_definitions()  # next_token은 statements에서 사용됨


# variable <var_list>;
def var_definition():
    global var_def_line

    var_def_line = ''  # 지역변수 선언문 초기화
    var_def_line += 'variable '
    var_list()

    executions.append(var_def_line)


# <var_list> -> <identifier> | <statement> <statements>
def var_list():
    global var_def_line

    lexical()
    if next_token == IDENT:
        var_def_line += token_string
        lexical()
        if next_token == COMMA:
            var_def_line += ', '
            var_list()
        elif next_token == SEMICOLON:
            pass


# <statements> -> <statement> | <statement> <statements>
def statements():
    statement()
    lexical()  # }를 만나면 statements 종료
    if next_token != RIGHT_BRACE:
        statements()


# <statement> -> call <identifier>; | print_ari; | <identifier>;
def statement():
    if next_token == CALL:  # call '함수명';
        lexical()  # 함수명
        executions.append(f'call {token_string}')
        lexical()  # 세미콜론

    elif next_token == PRINTARI:  # print_ari;
        executions.append(f'print_ari')
        # print_ari의 기능 수행
        lexical()  # 세미콜론

    elif next_token == IDENT:  # q;
        executions.append(f'{token_string}')  # 실행문 리스트에 추가
        lexical()  # 세미콜론


def execute(fn):  # 함수명이 주어지면 이 함수를 실행
    global func_dict, ra, dn, nums
    addr = -1  # 현재 실행문의 주소

    exe_list = func_dict[fn]  # 해당 함수의 실행문 리스트
    v_list = []  # 지역 변수를 추출하여 리스트로

    for i in range(len(exe_list)):

        if 'variable' in exe_list[i]:  # 변수 선언문이라면
            temp = exe_list[i].replace('variable', '')  # 지역변수 추출
            for t in temp:
                if t.isalpha():
                    v_list.append(t)

            if fn == 'main':  # 메인문이라면 지역변수로만 이루어진 ARI를 가짐
                main_ari = Ari(local_variables=v_list)
                ari_stack.append(main_ari)
                func_name_stack.append(fn)
                nums = len(v_list)

            else:  # main문이 아닌 함수의 ARI 생성
                func_name_stack.append(fn)
                this_ari = Ari(return_addr=ra, dynamic_link=dn, local_variables=v_list)
                ari_stack.append(this_ari)
                dn += nums

        elif 'print_ari' in exe_list[i]:  # print_ari
            addr += 1

            temp_ari = ari_stack[::-1]  # ari_stack을 역순으로 읽어옴. second -> first -> main순
            for j in range(len(temp_ari)):
                print(f'{func_name_stack[::-1][j]}:')

                if temp_ari[j]['return_addr'] == None:  # main's ARI
                    for k in temp_ari[j]['local_variables'][::-1]:
                        print(f'Local variable: {k}')
                    print()

                else:
                    for k in temp_ari[j]['local_variables'][::-1]:
                        print(f'Local variable: {k}')
                    print(f"Dynamic Link: {temp_ari[j]['dynamic_link']}")
                    print(f"Return Address: {temp_ari[j]['return_addr']}\n")


        elif 'call' in exe_list[i]:  # call '함수명'
            addr += 1
            temp = exe_list[i].replace('call', '')
            f_name = ''  # '함수명' 추출
            for t in temp:
                if t.isalpha():
                    f_name += t

            ra = fn + ': ' + str(addr + 1)  # return address 지정

            if f_name in func_dict:
                execute(f_name)  # '함수명' 호출



        else:  # 변수명을 호출한 경우
            link_cnt = 0
            idx_now = func_name_stack.index(fn)

            for p in range(len(ari_stack)):  # link_count 구하기
                if exe_list[i] in ari_stack[p]['local_variables']:
                    link_cnt = idx_now - p

            print(f'{fn}:{exe_list[i]} => {link_cnt}, {get_loc_off(exe_list[i])}\n')


def get_loc_off(c):
    for i in range(len(ari_stack)):

        if ari_stack[i]['return_addr'] == None and c in ari_stack[i]['local_variables']:  # main의 ARI
            return ari_stack[i]['local_variables'].index(c)

        else:
            if c in ari_stack[i]['local_variables']:
                return ari_stack[i]['local_variables'].index(c) + 2


####################################################################################

if len(sys.argv) != 2:
    print("Insufficient arguments")
    sys.exit()

file_path = sys.argv[1]

# main
try:
    file = open(file_path, 'r', encoding="utf-8")
except FileNotFoundError:
    print("ERROR - file doesn't exits")
else:
    data = list(file.read())
    data.append('$')  # 파일의 끝 표시. $ (EOF)
    file.close()

    start()

    if 'main' in func_dict and has_error == False:
        print("Syntax O.K.\n")
        execute('main')
    else:  # main함수가 없는 경우
        print('No starting function.')
