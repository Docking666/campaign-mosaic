"""
通知推送模块
支持邮件、飞书机器人、钉钉机器人、企业微信机器人
"""

import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional

import requests


class NotificationManager:
    """多渠道通知推送管理器"""

    def __init__(self, config: dict):
        """
        Args:
            config: config.yaml 中 notifications 段的配置
        """
        self.config = config
        self.errors = []

    def send_all(self, subject: str, html_content: str, md_content: str = ""):
        """发送所有已启用的通知渠道"""
        results = {}

        # 邮件通知
        email_config = self.config.get("email", {})
        if email_config.get("enabled", False):
            results["email"] = self._send_email(subject, html_content, email_config)

        # 飞书机器人
        feishu_config = self.config.get("feishu_bot", {})
        if feishu_config.get("enabled", False) and feishu_config.get("webhook_url"):
            results["feishu"] = self._send_feishu(md_content or self._html_to_simple_md(html_content), feishu_config)

        # 钉钉机器人
        dingtalk_config = self.config.get("dingtalk_bot", {})
        if dingtalk_config.get("enabled", False) and dingtalk_config.get("webhook_url"):
            results["dingtalk"] = self._send_dingtalk(md_content or self._html_to_simple_md(html_content), dingtalk_config)

        # 企业微信机器人
        wecom_config = self.config.get("wecom_bot", {})
        if wecom_config.get("enabled", False) and wecom_config.get("webhook_url"):
            results["wecom"] = self._send_wecom(md_content or self._html_to_simple_md(html_content), wecom_config)

        return results

    def send_alert(self, message: str):
        """发送异常告警"""
        alert_content = f"⚠️ **CampaignMosaic 告警**\n\n{message}"

        feishu_config = self.config.get("feishu_bot", {})
        if feishu_config.get("enabled", False) and feishu_config.get("webhook_url"):
            self._send_feishu(alert_content, feishu_config)

        dingtalk_config = self.config.get("dingtalk_bot", {})
        if dingtalk_config.get("enabled", False) and dingtalk_config.get("webhook_url"):
            self._send_dingtalk(alert_content, dingtalk_config)

        wecom_config = self.config.get("wecom_bot", {})
        if wecom_config.get("enabled", False) and wecom_config.get("webhook_url"):
            self._send_wecom(alert_content, wecom_config)

    def _send_email(self, subject: str, html_content: str, config: dict) -> bool:
        """发送邮件通知"""
        try:
            smtp_server = config.get("smtp_server", "")
            smtp_port = config.get("smtp_port", 465)
            sender = config.get("sender", "")
            password = config.get("password", "")
            receivers = config.get("receivers", [])

            if not all([smtp_server, sender, receivers]):
                print("[Notification] 邮件配置不完整，跳过发送")
                return False

            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = sender
            msg["To"] = ", ".join(receivers)

            msg.attach(MIMEText(html_content, "html", "utf-8"))

            with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                server.login(sender, password)
                server.sendmail(sender, receivers, msg.as_string())

            print(f"[Notification] 邮件发送成功: {len(receivers)} 收件人")
            return True

        except Exception as e:
            error_msg = f"邮件发送失败: {e}"
            print(f"[Notification] {error_msg}")
            self.errors.append(error_msg)
            return False

    def _send_feishu(self, content: str, config: dict) -> bool:
        """发送飞书机器人消息"""
        try:
            webhook_url = config.get("webhook_url", "")
            payload = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {"tag": "plain_text", "content": "📊 CampaignMosaic 日报"},
                        "template": "blue",
                    },
                    "elements": [
                        {
                            "tag": "markdown",
                            "content": content[:2000],  # 飞书消息长度限制
                        }
                    ],
                },
            }

            response = requests.post(webhook_url, json=payload, timeout=10)
            result = response.json()

            if result.get("code") == 0 or result.get("StatusCode") == 0:
                print("[Notification] 飞书消息发送成功")
                return True
            else:
                print(f"[Notification] 飞书消息发送失败: {result}")
                return False

        except Exception as e:
            error_msg = f"飞书消息发送失败: {e}"
            print(f"[Notification] {error_msg}")
            self.errors.append(error_msg)
            return False

    def _send_dingtalk(self, content: str, config: dict) -> bool:
        """发送钉钉机器人消息"""
        try:
            webhook_url = config.get("webhook_url", "")
            secret = config.get("secret", "")

            # 如果有签名密钥，计算签名
            if secret:
                import time
                import hmac
                import hashlib
                import base64
                import urllib.parse

                timestamp = str(round(time.time() * 1000))
                string_to_sign = f"{timestamp}\n{secret}"
                hmac_code = hmac.new(
                    secret.encode("utf-8"),
                    string_to_sign.encode("utf-8"),
                    digestmod=hashlib.sha256,
                ).digest()
                sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
                webhook_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"

            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": "📊 CampaignMosaic 日报",
                    "text": content[:15000],
                },
            }

            response = requests.post(webhook_url, json=payload, timeout=10)
            result = response.json()

            if result.get("errcode") == 0:
                print("[Notification] 钉钉消息发送成功")
                return True
            else:
                print(f"[Notification] 钉钉消息发送失败: {result}")
                return False

        except Exception as e:
            error_msg = f"钉钉消息发送失败: {e}"
            print(f"[Notification] {error_msg}")
            self.errors.append(error_msg)
            return False

    def _send_wecom(self, content: str, config: dict) -> bool:
        """发送企业微信机器人消息"""
        try:
            webhook_url = config.get("webhook_url", "")

            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "content": content[:4096],  # 企微消息长度限制
                },
            }

            response = requests.post(webhook_url, json=payload, timeout=10)
            result = response.json()

            if result.get("errcode") == 0:
                print("[Notification] 企业微信消息发送成功")
                return True
            else:
                print(f"[Notification] 企业微信消息发送失败: {result}")
                return False

        except Exception as e:
            error_msg = f"企业微信消息发送失败: {e}"
            print(f"[Notification] {error_msg}")
            self.errors.append(error_msg)
            return False

    def _html_to_simple_md(self, html: str) -> str:
        """将HTML内容简单转换为Markdown文本（用于IM推送）"""
        import re
        # 简单去除HTML标签
        text = re.sub(r"<[^>]+>", "", html)
        # 清理多余空白
        text = re.sub(r"\s+", " ", text).strip()
        return text[:2000]
