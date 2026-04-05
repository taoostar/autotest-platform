#!/bin/bash
# SSL证书生成脚本

# 创建SSL目录
mkdir -p /etc/nginx/ssl

# 生成自签名证书（仅用于测试）
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/ssl/autotest.key \
    -out /etc/nginx/ssl/autotest.crt \
    -subj "/C=CN/ST=Beijing/L=Beijing/O=AutoTest/CN=autotest.example.com"

echo "自签名证书已生成到 /etc/nginx/ssl/"
echo ""
echo "对于生产环境，建议使用 Let's Encrypt:"
echo "  apt install certbot python3-certbot-nginx"
echo "  certbot --nginx -d autotest.example.com"
echo ""
echo "请将 nginx/autotest.conf 复制到 /etc/nginx/sites-available/"
echo "  sudo cp /home/litao/autotest/nginx/autotest.conf /etc/nginx/sites-available/"
echo "  sudo ln -s /etc/nginx/sites-available/autotest.conf /etc/nginx/sites-enabled/"
echo "  sudo nginx -t"
echo "  sudo systemctl reload nginx"