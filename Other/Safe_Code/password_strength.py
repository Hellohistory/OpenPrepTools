def translate_suggestion(suggestion):
    translations = {
        "Use a few words, avoid common phrases": "使用几个单词，避免常见短语",
        "No need for symbols, digits, or uppercase letters": "不需要符号、数字或大写字母",
        "Add another word or two. Uncommon words are better.": "再添加一个或两个单词。不常见的词更好。",
        "Straight rows of keys are easy to guess": "直排键很容易被猜到",
        "Short keyboard patterns are easy to guess": "短键盘图案很容易被猜到",
        "Use a longer keyboard pattern with more turns": "使用更长的键盘图案，多转几次",
        "Avoid repeated words and characters": "避免重复的单词和字符",
        "Avoid sequences": "避免顺序",
        "Avoid recent years": "避免使用最近的年份",
        "Avoid years that are associated with you": "避免使用与你相关的年份",
        "Avoid dates and years that are associated with you": "避免使用与你相关的日期和年份",
        "Avoid repeated words and chaacters": "避免重复的单词和字符",
        "Capitalization doesn't help very much": "大写帮助不大",
        "All-uppercase is almost as easy to guess as all-lowercase": "全大写几乎和全小写一样容易猜到",
        "Reversed words aren't much harder to guess": "反转单词并没有难多少",
        "Predictable substitutions like '@' instead of 'a' don't help very much": "可预测的替换（如 '@' 代替 'a'）帮助不大"
    }
    return translations.get(suggestion, suggestion)

