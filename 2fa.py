#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TOTP验证码生成器，github Two-factor authentication
"""

import os
import sys
import time
import json
import getpass
import argparse
from pathlib import Path

try:
    import pyotp
    import qrcode
except ImportError:
    print("请先安装必要的依赖包:")
    print("pip install pyotp qrcode[pil]")
    sys.exit(1)


class TOTPManager:
    def __init__(self):
        self.config_dir = os.getcwd()
        self.config_file = os.path.join(self.config_dir, 'totp_accounts.json')
        self.accounts = self._load_accounts()
    
    def _load_accounts(self):
        """加载已保存的账户"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_accounts(self):
        """保存账户到配置文件"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.accounts, f, indent=2, ensure_ascii=False)
        except IOError as e:
            print(f"保存配置文件失败: {e}")
    
    def add_account(self, name, secret, issuer=None):
        """添加新账户"""
        if name in self.accounts:
            overwrite = input(f"账户 '{name}' 已存在，是否覆盖? (y/N): ")
            if overwrite.lower() != 'y':
                return False
        
        self.accounts[name] = {
            'secret': secret,
            'issuer': issuer or name
        }
        self._save_accounts()
        print(f"账户 '{name}' 添加成功!")
        return True
    
    def remove_account(self, name):
        """删除账户"""
        if name in self.accounts:
            del self.accounts[name]
            self._save_accounts()
            print(f"账户 '{name}' 删除成功!")
            return True
        else:
            print(f"账户 '{name}' 不存在!")
            return False
    
    def list_accounts(self):
        """列出所有账户"""
        if not self.accounts:
            print("没有保存的账户")
            return
        
        print("保存的账户:")
        for name, info in self.accounts.items():
            print(f"  - {name} ({info.get('issuer', name)})")
    
    def generate_code(self, name):
        """生成指定账户的TOTP验证码"""
        if name not in self.accounts:
            print(f"账户 '{name}' 不存在!")
            return None
        
        secret = self.accounts[name]['secret']
        totp = pyotp.TOTP(secret)
        code = totp.now()
        remaining = 30 - (int(time.time()) % 30)
        
        return code, remaining
    
    def generate_all_codes(self):
        """生成所有账户的TOTP验证码"""
        if not self.accounts:
            print("没有保存的账户")
            return
        
        current_time = int(time.time())
        remaining = 30 - (current_time % 30)
        
        print(f"TOTP验证码 (剩余时间: {remaining}秒):")
        print("-" * 40)
        
        for name, info in self.accounts.items():
            secret = info['secret']
            totp = pyotp.TOTP(secret)
            code = totp.now()
            issuer = info.get('issuer', name)
            print(f"{name:20} {code:>6} ({issuer})")
    
    def generate_qr_code(self, name):
        """生成二维码"""
        if name not in self.accounts:
            print(f"账户 '{name}' 不存在!")
            return
        
        account_info = self.accounts[name]
        secret = account_info['secret']
        issuer = account_info.get('issuer', name)
        
        totp = pyotp.TOTP(secret)
        provisioning_uri = totp.provisioning_uri(
            name=name,
            issuer_name=issuer
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(provisioning_uri)
        qr.make(fit=True)
        
        # 在控制台显示二维码
        qr.print_ascii()
        
        # 保存二维码图片
        img = qr.make_image(fill_color="black", back_color="white")
        qr_file = self.config_dir / f"{name}_qr.png"
        img.save(qr_file)
        print(f"二维码已保存到: {qr_file}")


def main():
    parser = argparse.ArgumentParser(description="跨平台TOTP验证码生成器")
    parser.add_argument("--add", "-a", help="添加新账户")
    parser.add_argument("--secret", "-s", help="账户密钥")
    parser.add_argument("--issuer", "-i", help="发行者名称")
    parser.add_argument("--remove", "-r", help="删除账户")
    parser.add_argument("--list", "-l", action="store_true", help="列出所有账户")
    parser.add_argument("--generate", "-g", help="生成指定账户的验证码")
    parser.add_argument("--all", action="store_true", help="生成所有账户的验证码")
    parser.add_argument("--qr", "-q", help="生成指定账户的二维码")
    parser.add_argument("--watch", "-w", action="store_true", help="实时监控模式")
    
    args = parser.parse_args()
    
    manager = TOTPManager()
    
    if args.add:
        if not args.secret:
            secret = getpass.getpass("请输入密钥 (输入时不显示): ")
        else:
            secret = args.secret
        
        manager.add_account(args.add, secret, args.issuer)
    
    elif args.remove:
        manager.remove_account(args.remove)
    
    elif args.list:
        manager.list_accounts()
    
    elif args.generate:
        result = manager.generate_code(args.generate)
        if result:
            code, remaining = result
            print(f"账户: {args.generate}")
            print(f"验证码: {code}")
            print(f"剩余时间: {remaining}秒")
    
    elif args.all:
        manager.generate_all_codes()
    
    elif args.qr:
        manager.generate_qr_code(args.qr)
    
    elif args.watch:
        print("实时监控模式 (按 Ctrl+C 退出)")
        try:
            while True:
                os.system('cls' if os.name == 'nt' else 'clear')
                manager.generate_all_codes()
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n退出监控模式")
    
    else:
        # 交互模式
        print("TOTP验证码生成器")
        print("支持平台: Windows, Linux, macOS")
        print("-" * 40)
        
        while True:
            print("\n选择操作:")
            print("1. 添加账户")
            print("2. 删除账户")
            print("3. 列出账户")
            print("4. 生成验证码")
            print("5. 生成所有验证码")
            print("6. 生成二维码")
            print("7. 实时监控")
            print("0. 退出")
            
            choice = input("\n请选择 (0-7): ").strip()
            
            if choice == "1":
                name = input("账户名称: ").strip()
                if name:
                    secret = getpass.getpass("密钥 (输入时不显示): ").strip()
                    issuer = input("发行者 (可选): ").strip() or None
                    manager.add_account(name, secret, issuer)
            
            elif choice == "2":
                manager.list_accounts()
                name = input("要删除的账户名称: ").strip()
                if name:
                    manager.remove_account(name)
            
            elif choice == "3":
                manager.list_accounts()
            
            elif choice == "4":
                manager.list_accounts()
                name = input("账户名称: ").strip()
                if name:
                    result = manager.generate_code(name)
                    if result:
                        code, remaining = result
                        print(f"验证码: {code}")
                        print(f"剩余时间: {remaining}秒")
            
            elif choice == "5":
                manager.generate_all_codes()
            
            elif choice == "6":
                manager.list_accounts()
                name = input("账户名称: ").strip()
                if name:
                    manager.generate_qr_code(name)
            
            elif choice == "7":
                print("实时监控模式 (按 Ctrl+C 返回菜单)")
                try:
                    while True:
                        os.system('cls' if os.name == 'nt' else 'clear')
                        manager.generate_all_codes()
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\n返回主菜单")
            
            elif choice == "0":
                print("再见!")
                break
            
            else:
                print("无效选择，请重新输入")


if __name__ == "__main__":
    main()