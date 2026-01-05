#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IPA安装服务 - iOS应用OTA安装
"""

import os
import uuid
from flask import Flask, render_template, request, send_file, url_for, jsonify
from werkzeug.utils import secure_filename
import plistlib

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# 创建上传目录
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

ALLOWED_EXTENSIONS = {'ipa'}

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """首页 - 显示上传表单"""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """处理IPA文件上传"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '没有选择文件'}), 400
    
    if file and allowed_file(file.filename):
        # 生成唯一ID
        app_id = str(uuid.uuid4())
        filename = secure_filename(file.filename)
        
        # 保存文件
        app_dir = os.path.join(app.config['UPLOAD_FOLDER'], app_id)
        os.makedirs(app_dir, exist_ok=True)
        
        file_path = os.path.join(app_dir, filename)
        file.save(file_path)
        
        # 获取应用信息
        app_name = request.form.get('app_name', filename.rsplit('.', 1)[0])
        bundle_id = request.form.get('bundle_id', 'com.example.app')
        version = request.form.get('version', '1.0.0')
        
        # 保存应用信息
        info = {
            'app_id': app_id,
            'filename': filename,
            'app_name': app_name,
            'bundle_id': bundle_id,
            'version': version
        }
        
        info_path = os.path.join(app_dir, 'info.plist')
        with open(info_path, 'wb') as f:
            plistlib.dump(info, f)
        
        # 生成安装链接
        install_url = url_for('install_page', app_id=app_id, _external=True)
        return jsonify({
            'success': True,
            'app_id': app_id,
            'install_url': install_url
        })
    
    return jsonify({'error': '不支持的文件类型'}), 400

@app.route('/install/<app_id>')
def install_page(app_id):
    """显示安装页面"""
    app_dir = os.path.join(app.config['UPLOAD_FOLDER'], app_id)
    info_path = os.path.join(app_dir, 'info.plist')
    
    if not os.path.exists(info_path):
        return "应用不存在", 404
    
    with open(info_path, 'rb') as f:
        info = plistlib.load(f)
    
    # 生成manifest.plist的URL
    manifest_url = url_for('manifest', app_id=app_id, _external=True, _scheme='https')
    if request.headers.get('X-Forwarded-Proto') != 'https':
        # 开发环境使用http
        manifest_url = url_for('manifest', app_id=app_id, _external=True)
    
    return render_template('install.html', 
                         app_name=info['app_name'],
                         bundle_id=info['bundle_id'],
                         version=info['version'],
                         app_id=app_id,
                         manifest_url=manifest_url)

@app.route('/manifest/<app_id>')
def manifest(app_id):
    """生成manifest.plist文件"""
    app_dir = os.path.join(app.config['UPLOAD_FOLDER'], app_id)
    info_path = os.path.join(app_dir, 'info.plist')
    
    if not os.path.exists(info_path):
        return "应用不存在", 404
    
    with open(info_path, 'rb') as f:
        info = plistlib.load(f)
    
    # 生成IPA文件的下载URL
    ipa_url = url_for('download', app_id=app_id, _external=True, _scheme='https')
    if request.headers.get('X-Forwarded-Proto') != 'https':
        ipa_url = url_for('download', app_id=app_id, _external=True)
    
    # 创建manifest.plist
    manifest_data = {
        'items': [
            {
                'assets': [
                    {
                        'kind': 'software-package',
                        'url': ipa_url
                    }
                ],
                'metadata': {
                    'bundle-identifier': info['bundle_id'],
                    'bundle-version': info['version'],
                    'kind': 'software',
                    'title': info['app_name']
                }
            }
        ]
    }
    
    return plistlib.dumps(manifest_data), 200, {
        'Content-Type': 'application/xml',
        'Content-Disposition': 'attachment; filename=manifest.plist'
    }

@app.route('/download/<app_id>')
def download(app_id):
    """下载IPA文件"""
    app_dir = os.path.join(app.config['UPLOAD_FOLDER'], app_id)
    info_path = os.path.join(app_dir, 'info.plist')
    
    if not os.path.exists(info_path):
        return "应用不存在", 404
    
    with open(info_path, 'rb') as f:
        info = plistlib.load(f)
    
    file_path = os.path.join(app_dir, info['filename'])
    return send_file(file_path, as_attachment=True, download_name=info['filename'])

if __name__ == '__main__':
    # 开发模式运行
    app.run(debug=True, host='0.0.0.0', port=5000)
