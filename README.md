# 游有IPA - iOS应用OTA安装服务

一个简单易用的iOS应用（IPA文件）在线安装服务，支持通过Web界面上传IPA文件并生成安装链接，用户可以通过Safari浏览器直接在iOS设备上安装应用。

## ✨ 特性

- 📦 **简单上传**：支持拖拽上传IPA文件
- 🔗 **一键生成**：自动生成安装链接和manifest.plist
- 📱 **OTA安装**：支持iOS设备通过Safari浏览器在线安装
- 🎨 **精美界面**：现代化的Web界面设计
- 🚀 **即开即用**：无需复杂配置，开箱即用

## 🚀 快速开始

### 环境要求

- Python 3.7+
- Flask 3.0+

### 安装

1. 克隆项目
```bash
git clone https://github.com/amjunliang/yueyouipa.git
cd yueyouipa
```

2. 安装依赖
```bash
pip install -r requirements.txt
```

3. 运行服务
```bash
python app.py
```

服务将在 `http://0.0.0.0:5000` 启动

### 使用方法

#### 1. 上传IPA文件

1. 访问首页 `http://your-server:5000`
2. 点击上传区域或拖拽IPA文件
3. 填写应用信息：
   - 应用名称
   - Bundle ID
   - 版本号
4. 点击"上传并生成安装链接"
5. 获取安装链接

#### 2. 在iOS设备上安装

1. 在iOS设备上使用Safari浏览器打开安装链接
2. 点击"点击安装"按钮
3. 确认安装
4. 安装完成后，前往"设置 > 通用 > VPN与设备管理"信任企业证书
5. 返回主屏幕打开应用

## 📁 项目结构

```
yueyouipa/
├── app.py              # Flask应用主文件
├── requirements.txt    # Python依赖
├── templates/          # HTML模板
│   ├── index.html     # 上传页面
│   └── install.html   # 安装页面
├── uploads/           # IPA文件存储目录（自动创建）
└── README.md          # 项目说明
```

## ⚙️ 配置

### 环境变量

- `SECRET_KEY`: Flask密钥（生产环境必须设置）
- 默认开发密钥：`dev-secret-key-change-in-production`

### 自定义配置

在 `app.py` 中可以修改以下配置：

```python
app.config['UPLOAD_FOLDER'] = 'uploads'  # 上传目录
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 最大文件大小（500MB）
```

## 🔒 安全说明

1. **生产环境部署**
   - 必须使用HTTPS协议（iOS要求）
   - 设置强密码的SECRET_KEY
   - 限制上传目录的访问权限

2. **证书要求**
   - IPA文件需要使用企业证书或开发者证书签名
   - 确保证书有效期内使用

3. **文件管理**
   - 定期清理过期的IPA文件
   - 设置上传文件大小限制
   - 验证上传文件类型

## 📝 API接口

### 上传IPA文件
```
POST /upload
Content-Type: multipart/form-data

参数:
- file: IPA文件
- app_name: 应用名称
- bundle_id: Bundle ID
- version: 版本号

返回:
{
  "success": true,
  "app_id": "uuid",
  "install_url": "http://domain/install/uuid"
}
```

### 获取安装页面
```
GET /install/<app_id>

返回: HTML安装页面
```

### 下载manifest.plist
```
GET /manifest/<app_id>

返回: application/xml
```

### 下载IPA文件
```
GET /download/<app_id>

返回: IPA文件
```

## 🌐 生产环境部署

### 使用Gunicorn部署

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

### 使用Nginx反向代理

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## ❓ 常见问题

### 1. 无法安装应用？

- 确保使用Safari浏览器打开安装链接
- 检查IPA文件是否使用有效证书签名
- 确认设备系统版本与应用兼容

### 2. 提示"无法下载应用"？

- 确保服务器使用HTTPS协议
- 检查manifest.plist文件URL是否正确
- 验证Bundle ID和应用签名是否匹配

### 3. 应用安装后无法打开？

- 前往"设置 > 通用 > VPN与设备管理"
- 找到对应的企业证书
- 点击"信任"

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request！

## 👤 作者

amjunliang

## 🔗 相关链接

- [iOS企业分发指南](https://developer.apple.com/documentation/devicemanagement/distributing_custom_apps)
- [Flask文档](https://flask.palletsprojects.com/)
