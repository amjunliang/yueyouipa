#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试脚本：验证IPA安装服务的核心功能
"""

import os
import sys
import tempfile
import plistlib
from io import BytesIO

# 添加项目路径
sys.path.insert(0, os.path.dirname(__file__))

import app

def test_app_configuration():
    """测试应用配置"""
    print("Testing app configuration...")
    assert app.app.config['UPLOAD_FOLDER'] is not None
    assert app.app.config['MAX_CONTENT_LENGTH'] > 0
    print("✓ App configuration is correct")

def test_allowed_file():
    """测试文件类型检查"""
    print("Testing file type validation...")
    assert app.allowed_file('test.ipa') == True
    assert app.allowed_file('test.IPA') == True
    assert app.allowed_file('test.apk') == False
    assert app.allowed_file('test.exe') == False
    assert app.allowed_file('test') == False
    print("✓ File type validation works correctly")

def test_routes_exist():
    """测试路由是否存在"""
    print("Testing routes...")
    client = app.app.test_client()
    
    # Test index page
    response = client.get('/')
    assert response.status_code == 200
    print("✓ Index page accessible")
    
    # Test upload endpoint (should fail without file)
    response = client.post('/upload')
    assert response.status_code == 400
    print("✓ Upload endpoint exists and validates input")

def test_file_upload_and_retrieval():
    """测试文件上传和检索流程"""
    print("Testing file upload and retrieval...")
    client = app.app.test_client()
    
    # Create a fake IPA file
    fake_ipa = BytesIO(b'This is a fake IPA file for testing')
    fake_ipa.name = 'test.ipa'
    
    # Upload file
    data = {
        'file': (fake_ipa, 'test.ipa'),
        'app_name': 'Test App',
        'bundle_id': 'com.test.app',
        'version': '1.0.0'
    }
    
    response = client.post('/upload', 
                          data=data,
                          content_type='multipart/form-data')
    
    assert response.status_code == 200
    json_data = response.get_json()
    assert 'app_id' in json_data
    assert 'install_url' in json_data
    
    app_id = json_data['app_id']
    print(f"✓ File uploaded successfully, app_id: {app_id}")
    
    # Test install page
    response = client.get(f'/install/{app_id}')
    assert response.status_code == 200
    assert b'Test App' in response.data
    print("✓ Install page accessible")
    
    # Test manifest
    response = client.get(f'/manifest/{app_id}')
    assert response.status_code == 200
    assert response.content_type == 'application/xml'
    
    # Parse manifest plist
    manifest = plistlib.loads(response.data)
    assert 'items' in manifest
    assert len(manifest['items']) > 0
    assert manifest['items'][0]['metadata']['bundle-identifier'] == 'com.test.app'
    print("✓ Manifest generated correctly")
    
    # Test download
    response = client.get(f'/download/{app_id}')
    assert response.status_code == 200
    print("✓ File download works")
    
    # Cleanup
    import shutil
    app_dir = os.path.join(app.app.config['UPLOAD_FOLDER'], app_id)
    if os.path.exists(app_dir):
        shutil.rmtree(app_dir)
    print("✓ Cleanup completed")

def test_nonexistent_app():
    """测试访问不存在的应用"""
    print("Testing nonexistent app handling...")
    client = app.app.test_client()
    
    fake_id = 'nonexistent-app-id'
    
    response = client.get(f'/install/{fake_id}')
    assert response.status_code == 404
    
    response = client.get(f'/manifest/{fake_id}')
    assert response.status_code == 404
    
    response = client.get(f'/download/{fake_id}')
    assert response.status_code == 404
    
    print("✓ Nonexistent app handled correctly")

def main():
    """运行所有测试"""
    print("=" * 50)
    print("IPA Installation Service - Test Suite")
    print("=" * 50)
    
    tests = [
        test_app_configuration,
        test_allowed_file,
        test_routes_exist,
        test_file_upload_and_retrieval,
        test_nonexistent_app
    ]
    
    failed = 0
    for test in tests:
        try:
            print(f"\n{test.__doc__}")
            test()
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {e}")
            failed += 1
    
    print("\n" + "=" * 50)
    if failed == 0:
        print("✓ All tests passed!")
        return 0
    else:
        print(f"✗ {failed} test(s) failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
