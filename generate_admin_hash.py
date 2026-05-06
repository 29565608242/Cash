from werkzeug.security import generate_password_hash

# 设置您的管理员密码
admin_password = 'your_password_here'  # 请替换为您想要的密码

# 生成密码哈希
password_hash = generate_password_hash(admin_password)
print(f"管理员密码哈希: {password_hash}")
print(f"请使用以下SQL语句创建管理员账户:")
print(f"INSERT INTO users (username, password_hash, is_admin) VALUES ('admin', '{password_hash}', 1);")