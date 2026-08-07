"""Email Service for sending transactional emails via Resend API."""

import logging
import resend
from core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Service for sending emails via Resend."""

    @staticmethod
    def _init_resend():
        """Initialize Resend API key."""
        if settings.RESEND_API_KEY:
            resend.api_key = settings.RESEND_API_KEY

    @classmethod
    def send_verification_email(cls, to_email: str, name: str, code: str) -> bool:
        """Send a 4-digit email verification code."""
        cls._init_resend()

        if not settings.RESEND_API_KEY:
            logger.warning(
                f"[MOCK EMAIL] Verification Code for {to_email}: {code}"
            )
            return True

        subject = "کد تایید حساب کاربری | آرتیسا"
        html_content = f"""
        <!DOCTYPE html>
        <html lang="fa" dir="rtl">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>کد تایید حساب کاربری</title>
          <style>
            body {{ font-family: 'Tahoma', 'Vazirmatn', Arial, sans-serif; background-color: #f4f4f7; margin: 0; padding: 20px; direction: rtl; text-align: right; }}
            .container {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.08); border: 1px solid #eaeaea; }}
            .header {{ background: linear-gradient(135deg, #111827 0%, #1f2937 100%); padding: 30px 20px; text-align: center; color: #ffffff; }}
            .header h1 {{ margin: 0; font-size: 24px; font-weight: 900; letter-spacing: 1px; color: #f3f4f6; }}
            .header p {{ margin: 5px 0 0 0; font-size: 12px; color: #9ca3af; }}
            .content {{ padding: 35px 30px; text-align: center; }}
            .greeting {{ font-size: 16px; font-weight: bold; color: #1f2937; margin-bottom: 12px; }}
            .text {{ font-size: 13px; color: #4b5563; line-height: 1.6; margin-bottom: 25px; }}
            .otp-box {{ background: #f9fafb; border: 2px dashed #e5e7eb; border-radius: 16px; padding: 20px; margin: 20px 0; text-align: center; }}
            .otp-code {{ font-size: 36px; font-weight: 900; letter-spacing: 12px; color: #4f46e5; margin: 0; direction: ltr; display: inline-block; }}
            .expiry {{ font-size: 11px; color: #ef4444; font-weight: bold; margin-top: 10px; }}
            .footer {{ background: #f9fafb; padding: 20px; text-align: center; font-size: 11px; color: #9ca3af; border-top: 1px solid #f3f4f6; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>آرتیسا | ARTISA</h1>
              <p>گالری آنلاین تابلو و هنر دیواری</p>
            </div>
            <div class="content">
              <div class="greeting">سلام {name} عزیز 👋</div>
              <div class="text">
                به آرتیسا خوش آمدید! جهت تکمیل ثبت‌نام و فعال‌سازی حساب کاربری خود، لطفاً کد تایید زیر را در برنامه وارد کنید:
              </div>
              <div class="otp-box">
                <div class="otp-code">{code}</div>
                <div class="expiry">⏱️ این کد تا ۱۰ دقیقه دیگر اعتبار دارد</div>
              </div>
              <div class="text" style="font-size: 11px; color: #9ca3af;">
                اگر شما این درخواست را ارسال نکرده‌اید، لطفاً این ایمیل را نادیده بگیرید.
              </div>
            </div>
            <div class="footer">
              © تمامی حقوق برای آرتیسا محفوظ است.
            </div>
          </div>
        </body>
        </html>
        """

        try:
            params = {
                "from": settings.FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }
            response = resend.Emails.send(params)
            logger.info(f"Verification email sent to {to_email}. ID: {response}")
            return True
        except Exception as e:
            logger.error(f"Failed to send verification email to {to_email}: {str(e)}")
            return False

    @classmethod
    def send_password_reset_email(cls, to_email: str, name: str, code: str) -> bool:
        """Send a 4-digit password reset verification code."""
        cls._init_resend()

        if not settings.RESEND_API_KEY:
            logger.warning(
                f"[MOCK EMAIL] Password Reset Code for {to_email}: {code}"
            )
            return True

        subject = "بازیابی رمز عبور | آرتیسا"
        html_content = f"""
        <!DOCTYPE html>
        <html lang="fa" dir="rtl">
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>بازیابی رمز عبور</title>
          <style>
            body {{ font-family: 'Tahoma', 'Vazirmatn', Arial, sans-serif; background-color: #f4f4f7; margin: 0; padding: 20px; direction: rtl; text-align: right; }}
            .container {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 20px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.08); border: 1px solid #eaeaea; }}
            .header {{ background: linear-gradient(135deg, #111827 0%, #1f2937 100%); padding: 30px 20px; text-align: center; color: #ffffff; }}
            .header h1 {{ margin: 0; font-size: 24px; font-weight: 900; letter-spacing: 1px; color: #f3f4f6; }}
            .header p {{ margin: 5px 0 0 0; font-size: 12px; color: #9ca3af; }}
            .content {{ padding: 35px 30px; text-align: center; }}
            .greeting {{ font-size: 16px; font-weight: bold; color: #1f2937; margin-bottom: 12px; }}
            .text {{ font-size: 13px; color: #4b5563; line-height: 1.6; margin-bottom: 25px; }}
            .otp-box {{ background: #fff5f5; border: 2px dashed #fca5a5; border-radius: 16px; padding: 20px; margin: 20px 0; text-align: center; }}
            .otp-code {{ font-size: 36px; font-weight: 900; letter-spacing: 12px; color: #dc2626; margin: 0; direction: ltr; display: inline-block; }}
            .expiry {{ font-size: 11px; color: #ef4444; font-weight: bold; margin-top: 10px; }}
            .footer {{ background: #f9fafb; padding: 20px; text-align: center; font-size: 11px; color: #9ca3af; border-top: 1px solid #f3f4f6; }}
          </style>
        </head>
        <body>
          <div class="container">
            <div class="header">
              <h1>آرتیسا | ARTISA</h1>
              <p>گالری آنلاین تابلو و هنر دیواری</p>
            </div>
            <div class="content">
              <div class="greeting">کاربر گرامی ({name}) 🔑</div>
              <div class="text">
                درخواستی برای بازیابی رمز عبور حساب کاربری شما ثبت شده است. جهت تغییر رمز عبور، کد تایید ۴ رقمی زیر را وارد کنید:
              </div>
              <div class="otp-box">
                <div class="otp-code">{code}</div>
                <div class="expiry">⏱️ این کد تا ۱۰ دقیقه دیگر اعتبار دارد</div>
              </div>
              <div class="text" style="font-size: 11px; color: #9ca3af;">
                اگر این درخواست توسط شما ثبت نشده است، رمز عبور شما تغییر نکرده و می‌توانید این ایمیل را نادیده بگیرید.
              </div>
            </div>
            <div class="footer">
              © تمامی حقوق برای آرتیسا محفوظ است.
            </div>
          </div>
        </body>
        </html>
        """

        try:
            params = {
                "from": settings.FROM_EMAIL,
                "to": [to_email],
                "subject": subject,
                "html": html_content,
            }
            response = resend.Emails.send(params)
            logger.info(f"Password reset email sent to {to_email}. ID: {response}")
            return True
        except Exception as e:
            logger.error(f"Failed to send password reset email to {to_email}: {str(e)}")
            return False
