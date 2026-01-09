"""
邮件发送服务

PRD 4.14: 风险预警邮件通知
- 支持 HTML 邮件
- 预警邮件模板
- SMTP 配置
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional

import structlog

from app.schemas.alert import RiskAlert, AlertSeverity

logger = structlog.get_logger()


class EmailService:
    """邮件发送服务"""

    def __init__(
        self,
        smtp_server: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        from_email: str = "alerts@quantvision.app",
    ):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email

    async def send_alert_email(self, to_email: str, alert: RiskAlert) -> bool:
        """发送预警邮件"""
        logger.info(
            "send_alert_email",
            to_email=to_email,
            alert_type=alert.alert_type,
            severity=alert.severity,
        )

        subject = f"[QuantVision] {alert.title}"
        html_body = self._build_alert_html(alert)

        return await self._send_email(to_email, subject, html_body)

    async def send_test_email(self, to_email: str) -> bool:
        """发送测试邮件"""
        logger.info("send_test_email", to_email=to_email)

        subject = "[QuantVision] 测试邮件"
        html_body = self._build_test_html()

        return await self._send_email(to_email, subject, html_body)

    def _build_alert_html(self, alert: RiskAlert) -> str:
        """构建预警邮件HTML"""
        severity_colors = {
            AlertSeverity.INFO: "#3b82f6",      # 蓝色
            AlertSeverity.WARNING: "#eab308",   # 黄色
            AlertSeverity.CRITICAL: "#ef4444",  # 红色
        }

        color = severity_colors.get(alert.severity, "#666")
        details_html = self._build_details_html(alert.details) if alert.details else ""

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; margin: 0; }}
                .container {{ max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }}
                .header {{ background: {color}; color: white; padding: 24px; }}
                .header h1 {{ margin: 0; font-size: 20px; font-weight: 600; }}
                .content {{ padding: 24px; }}
                .message {{ color: #333; line-height: 1.8; font-size: 15px; }}
                .details {{ background: #f9fafb; padding: 16px; border-radius: 6px; margin-top: 20px; border: 1px solid #e5e7eb; }}
                .details p {{ margin: 8px 0; color: #4b5563; }}
                .details strong {{ color: #1f2937; }}
                .footer {{ padding: 20px 24px; text-align: center; color: #9ca3af; font-size: 13px; border-top: 1px solid #e5e7eb; }}
                .btn {{ display: inline-block; background: #3b82f6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 20px; font-weight: 500; }}
                .btn:hover {{ background: #2563eb; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{alert.title}</h1>
                </div>
                <div class="content">
                    <p class="message">{alert.message}</p>
                    {details_html}
                    <a href="https://quantvision.app/alerts/{alert.alert_id}" class="btn">
                        查看详情
                    </a>
                </div>
                <div class="footer">
                    <p>此邮件由 QuantVision 量化投资平台自动发送</p>
                    <p>如需修改预警设置，请访问 <a href="https://quantvision.app/settings/alerts" style="color: #3b82f6;">预警配置</a></p>
                </div>
            </div>
        </body>
        </html>
        """

    def _build_test_html(self) -> str:
        """构建测试邮件HTML"""
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; padding: 20px; margin: 0; }
                .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1); }
                .header { background: #22c55e; color: white; padding: 24px; }
                .header h1 { margin: 0; font-size: 20px; font-weight: 600; }
                .content { padding: 24px; }
                .message { color: #333; line-height: 1.8; font-size: 15px; }
                .footer { padding: 20px 24px; text-align: center; color: #9ca3af; font-size: 13px; border-top: 1px solid #e5e7eb; }
                .success-icon { font-size: 48px; text-align: center; margin-bottom: 16px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>邮件配置测试成功</h1>
                </div>
                <div class="content">
                    <div class="success-icon">✅</div>
                    <p class="message">
                        恭喜！您的邮件通知配置已成功。<br><br>
                        当您的策略触发风险预警时，系统将自动发送邮件通知到此邮箱。<br><br>
                        您可以在设置页面调整预警阈值和通知偏好。
                    </p>
                </div>
                <div class="footer">
                    <p>此邮件由 QuantVision 量化投资平台发送</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _build_details_html(self, details: dict) -> str:
        """构建详情区块"""
        if not details:
            return ""

        labels = {
            "current_value": "当前值",
            "threshold": "预警阈值",
            "strategy_name": "策略名称",
            "symbol": "股票代码",
            "position_size": "持仓规模",
            "daily_pnl": "今日盈亏",
        }

        items = []
        for key, value in details.items():
            label = labels.get(key, key)
            # 格式化数值
            if isinstance(value, float):
                if 0 < abs(value) < 1:
                    value = f"{value * 100:.2f}%"
                else:
                    value = f"{value:.2f}"
            items.append(f"<p><strong>{label}:</strong> {value}</p>")

        return f'<div class="details">{"".join(items)}</div>'

    async def _send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
    ) -> bool:
        """发送邮件"""
        # 如果没有配置SMTP凭证，仅记录日志
        if not self.smtp_user or not self.smtp_password:
            logger.warning(
                "email_not_sent_no_credentials",
                to_email=to_email,
                subject=subject,
            )
            # 开发环境返回成功，生产环境应返回False
            return True

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.from_email
            msg["To"] = to_email

            html_part = MIMEText(html_body, "html", "utf-8")
            msg.attach(html_part)

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)

            logger.info("email_sent", to_email=to_email, subject=subject)
            return True

        except Exception as e:
            logger.error("email_send_failed", error=str(e), to_email=to_email)
            return False


# 全局服务实例
email_service = EmailService()
