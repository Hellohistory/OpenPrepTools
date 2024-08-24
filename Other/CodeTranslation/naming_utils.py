# naming_utils.py

def format_variable_name(english_name, style='snake_case', prefix='', suffix='', unit='', reverse=False,
                         sequence_num=None, type_suffix=''):
    words = english_name.split()

    if reverse:
        words = [word[::-1] for word in words]

    if style == 'snake_case':
        name = '_'.join(words).lower()

    elif style == 'camelCase':
        name = words[0].lower() + ''.join(word.capitalize() for word in words[1:])

    elif style == 'PascalCase':
        name = ''.join(word.capitalize() for word in words)

    elif style == 'CONSTANT_CASE':
        name = '_'.join(words).upper()

    elif style == 'kebab-case':
        name = '-'.join(words).lower()

    elif style == 'dot.case':
        name = '.'.join(words).lower()

    elif style == 'SCREAMING_SNAKE_CASE':
        name = '_'.join(words).upper()

    elif style == 'train-case':
        name = '-'.join(word.capitalize() for word in words)

    elif style == 'UPPERCASE':
        name = ''.join(words).upper()

    elif style == 'lowercase':
        name = ''.join(words).lower()

    elif style == 'Hungarian_Notation':
        name = prefix + ''.join(word.capitalize() for word in words)

    elif style == 'GreekCase':
        name = prefix + '_'.join(words).lower()

    elif style == 'm_member_variable':
        name = 'm_' + '_'.join(words).lower()

    elif style == 'Capitalized Words':
        name = ' '.join(word.capitalize() for word in words)

    elif style == 'Title Case':
        name = ''.join(word.title() for word in words)

    elif style == 'SNAKE_CASE':
        name = '_'.join(words).upper()

    elif style == 'SCREAMING_KEBAB_CASE':
        name = '-'.join(words).upper()

    elif style == 'path/case':
        name = '/'.join(words).lower()

    elif style == 'MixedCase':
        name = words[0].capitalize() + ''.join(word.capitalize() for word in words[1:])

    elif style == 'BacktickCase':
        name = f"`{'_'.join(words)}`"

    elif style == 'SuffixNotation':
        name = '_'.join(words) + f"_{type_suffix}"

    elif style == 'NumberedCamelCase':
        name = words[0].lower() + ''.join(word.capitalize() for word in words[1:]) + str(sequence_num)

    elif style == 'DotCaseWithTypeSuffix':
        name = '.'.join(words).lower() + f".{type_suffix}"

    elif style == 'spaced-case':
        name = ' '.join(words).lower()

    elif style == 'HashCase':
        name = '#'.join(words).lower()

    elif style == 'DollarCase':
        name = '$'.join(words).lower()

    elif style == 'TildeCase':
        name = '~'.join(words).lower()

    elif style == 'UnderscoreCamelCase':
        name = words[0].lower() + ''.join(word.capitalize() for word in words[1:]) + '_'

    elif style == 'AtSignCase':
        name = '@'.join(words).lower()

    elif style == 'ColonCase':
        name = ':'.join(words).lower()

    elif style == 'AmpersandCase':
        name = '&'.join(words).lower()

    elif style == 'PercentCase':
        name = '%'.join(words).lower()

    elif style == 'ReversedWordsCase':
        name = ' '.join(words[::-1])

    elif style == 'SpaceCaseWithTypePrefix':
        name = f"{type_suffix} " + ' '.join(words).lower()

    elif style == 'BracketCase':
        name = ''.join(f"[{word}]" for word in words)

    elif style == 'SlashCase':
        name = '\\'.join(words)

    elif style == 'PascalSnakeCase':
        name = '_'.join(word.capitalize() for word in words)

    elif style == 'PlusCase':
        name = '+'.join(words).lower()

    elif style == 'CaretCase':
        name = '^'.join(words).lower()

    elif style == 'AngleBracketCase':
        name = ''.join(f"<{word}>" for word in words)

    elif style == 'PoundCase':
        name = f"#{'_'.join(words).lower()}#"

    elif style == 'NumberedSnakeCase':
        name = f"{sequence_num}_{'_'.join(words).lower()}"

    elif style == 'ExclamationCase':
        name = '!'.join(words).lower()

    else:
        raise ValueError("不支持的命名风格")

    if sequence_num is not None and style not in ['NumberedCamelCase']:
        name = f"{name}_{sequence_num}"

    if type_suffix and style not in ['SuffixNotation', 'DotCaseWithTypeSuffix', 'SpaceCaseWithTypePrefix']:
        name = f"{name}_{type_suffix}"

    if unit:
        name = f"{name}_{unit}"

    return f"{prefix}{name}{suffix}"


NAMING_STYLES = [
    "snake_case", "camelCase", "PascalCase", "CONSTANT_CASE", "kebab-case",
    "dot.case", "SCREAMING_SNAKE_CASE", "train-case", "UPPERCASE",
    "lowercase", "Hungarian_Notation", "GreekCase", "m_member_variable",
    "Capitalized Words", "Title Case", "SNAKE_CASE", "SCREAMING_KEBAB_CASE",
    "path/case", "MixedCase", "BacktickCase", "SuffixNotation",
    "NumberedCamelCase", "DotCaseWithTypeSuffix", "spaced-case", "HashCase",
    "DollarCase", "TildeCase", "UnderscoreCamelCase", "AtSignCase", "ColonCase",
    "AmpersandCase", "PercentCase", "ReversedWordsCase",
    "SpaceCaseWithTypePrefix", "BracketCase", "SlashCase", "PascalSnakeCase", "PlusCase", "CaretCase",
    "AngleBracketCase", "PoundCase", "NumberedSnakeCase", "ExclamationCase"
]
