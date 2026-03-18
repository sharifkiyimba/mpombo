with open('app.py', 'r', encoding='utf-8') as f:
    content = f.read()

old = 'from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash'
new = 'from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash\nimport pymysql\npymysql.install_as_MySQLdb()'

if 'pymysql' not in content:
    content = content.replace(old, new, 1)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("FIXED - pymysql added")
else:
    print("Already has pymysql")

lines = content.split('\n')[:5]
for i, l in enumerate(lines, 1):
    print(f"{i}: {l}")
