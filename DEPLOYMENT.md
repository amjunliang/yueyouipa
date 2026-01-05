# 部署指南 (Deployment Guide)

本文档介绍如何在生产环境中部署游有IPA安装服务。

## 环境要求

- Python 3.7+
- Nginx (推荐用作反向代理)
- SSL证书 (iOS OTA安装必需HTTPS)
- 至少1GB RAM
- 足够的磁盘空间存储IPA文件

## 生产环境部署步骤

### 1. 准备服务器

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装Python和相关工具
sudo apt install python3 python3-pip python3-venv nginx -y
```

### 2. 部署应用

```bash
# 创建应用目录
sudo mkdir -p /var/www/yueyouipa
cd /var/www/yueyouipa

# 克隆代码
git clone https://github.com/amjunliang/yueyouipa.git .

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
pip install gunicorn
```

### 3. 配置环境变量

创建 `/var/www/yueyouipa/.env` 文件：

```bash
# 生产环境密钥 (使用以下命令生成)
# python3 -c "import secrets; print(secrets.token_urlsafe(32))"
SECRET_KEY=your-secure-secret-key-here

# Flask环境
FLASK_ENV=production

# 可选：启用调试模式（仅开发环境）
# FLASK_DEBUG=false
```

### 4. 创建Systemd服务

创建 `/etc/systemd/system/yueyouipa.service`:

```ini
[Unit]
Description=YueyouIPA - iOS App Installation Service
After=network.target

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/var/www/yueyouipa
Environment="PATH=/var/www/yueyouipa/venv/bin"
EnvironmentFile=/var/www/yueyouipa/.env
ExecStart=/var/www/yueyouipa/venv/bin/gunicorn --workers 4 --bind 127.0.0.1:5000 --access-logfile /var/log/yueyouipa/access.log --error-logfile /var/log/yueyouipa/error.log app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

创建日志目录：

```bash
sudo mkdir -p /var/log/yueyouipa
sudo chown www-data:www-data /var/log/yueyouipa
```

启动服务：

```bash
# 设置权限
sudo chown -R www-data:www-data /var/www/yueyouipa

# 启用并启动服务
sudo systemctl daemon-reload
sudo systemctl enable yueyouipa
sudo systemctl start yueyouipa

# 检查状态
sudo systemctl status yueyouipa
```

### 5. 配置Nginx反向代理

创建 `/etc/nginx/sites-available/yueyouipa`:

```nginx
# HTTP - 重定向到HTTPS
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS
server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL证书配置
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # SSL安全配置
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # 文件上传大小限制 (500MB)
    client_max_body_size 500M;
    
    # 超时设置
    client_body_timeout 300s;
    proxy_read_timeout 300s;
    
    # 日志
    access_log /var/log/nginx/yueyouipa-access.log;
    error_log /var/log/nginx/yueyouipa-error.log;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Ssl on;
        
        # WebSocket支持（如需要）
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

启用配置：

```bash
# 创建符号链接
sudo ln -s /etc/nginx/sites-available/yueyouipa /etc/nginx/sites-enabled/

# 测试配置
sudo nginx -t

# 重启Nginx
sudo systemctl restart nginx
```

### 6. 获取SSL证书

使用Let's Encrypt获取免费SSL证书：

```bash
# 安装Certbot
sudo apt install certbot python3-certbot-nginx -y

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

## 安全建议

### 1. 文件存储

定期清理过期的IPA文件：

```bash
# 创建清理脚本 /usr/local/bin/cleanup-ipa.sh
#!/bin/bash
find /var/www/yueyouipa/uploads -type d -mtime +7 -exec rm -rf {} \;

# 添加到crontab (每天凌晨3点执行)
0 3 * * * /usr/local/bin/cleanup-ipa.sh
```

### 2. 防火墙配置

```bash
# 只开放必要端口
sudo ufw allow 22/tcp   # SSH
sudo ufw allow 80/tcp   # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable
```

### 3. 监控和日志

```bash
# 查看应用日志
sudo journalctl -u yueyouipa -f

# 查看Nginx日志
sudo tail -f /var/log/nginx/yueyouipa-access.log
sudo tail -f /var/log/nginx/yueyouipa-error.log
```

## 更新应用

```bash
cd /var/www/yueyouipa
git pull
source venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart yueyouipa
```

## 故障排查

### 服务无法启动

```bash
# 检查服务状态
sudo systemctl status yueyouipa

# 查看详细日志
sudo journalctl -u yueyouipa -n 50

# 检查端口占用
sudo netstat -tulpn | grep 5000
```

### 上传失败

1. 检查磁盘空间：`df -h`
2. 检查uploads目录权限：`ls -la /var/www/yueyouipa/uploads`
3. 检查Nginx配置：`client_max_body_size`

### SSL证书问题

```bash
# 检查证书有效期
sudo certbot certificates

# 手动续期
sudo certbot renew
```

## 性能优化

### 1. Gunicorn工作进程

根据CPU核心数调整workers：

```bash
workers = (2 * CPU cores) + 1
```

### 2. Nginx缓存

在Nginx配置中添加：

```nginx
location /static/ {
    alias /var/www/yueyouipa/static/;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

### 3. 使用CDN

将静态文件上传到CDN，提高访问速度。

## 备份策略

定期备份uploads目录：

```bash
#!/bin/bash
# /usr/local/bin/backup-ipa.sh
tar -czf /backup/yueyouipa-$(date +%Y%m%d).tar.gz /var/www/yueyouipa/uploads
```

## 支持

如有问题，请提交Issue：https://github.com/amjunliang/yueyouipa/issues
