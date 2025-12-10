class SendAuthHandler():
    email_code=

    def send_email(self, email_code):
        title = "메일 제목 입력"
        content = {
            "message": "메일 내용 입력",
        }
        receive_email = [User.Email(email_code)]
        from_email = "발송하는 메일 정보 입력"
        emailContent = render_to_string("email.html", content)

        emailObject = EmailMessage(subject=title, body=emailContent, to="EMAIL_HOST_USER", from_email=from_email)
        emailObject.content_subtype = "html"
        emailObject.send()


def send_sms(self, sms_code):
        pass

