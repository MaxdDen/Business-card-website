#!/usr/bin/env python3
"""
Исправление init.sql
"""

def fix_init_sql():
    """Исправить проблемы в init.sql"""
    
    with open('app/database/init.sql', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 Анализируем init.sql...")
    
    # Проверяем на проблемы с кодировкой
    problems = []
    
    # Проверяем на незакрытые кавычки
    single_quotes = content.count("'")
    if single_quotes % 2 != 0:
        problems.append("Нечетное количество одинарных кавычек")
    
    # Проверяем на незакрытые скобки
    open_parens = content.count('(')
    close_parens = content.count(')')
    if open_parens != close_parens:
        problems.append(f"Несоответствие скобок: {open_parens} открывающих, {close_parens} закрывающих")
    
    # Проверяем на проблемы с INSERT
    insert_count = content.count('INSERT OR IGNORE INTO texts')
    semicolon_count = content.count(');')
    
    print(f"📊 Статистика:")
    print(f"  - INSERT блоков: {insert_count}")
    print(f"  - Закрывающих ); : {semicolon_count}")
    print(f"  - Одинарных кавычек: {single_quotes}")
    print(f"  - Открывающих скобок: {open_parens}")
    print(f"  - Закрывающих скобок: {close_parens}")
    
    if problems:
        print("❌ Найдены проблемы:")
        for problem in problems:
            print(f"  - {problem}")
        return False
    else:
        print("✅ Проблем не найдено")
        return True

if __name__ == "__main__":
    success = fix_init_sql()
    exit(0 if success else 1)
