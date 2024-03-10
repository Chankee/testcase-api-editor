import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.header import Header


def mailrelay(title,to, cc,content,type='plain'):
    msg = MIMEText(content.encode('utf-8'), type, "utf-8")  # plain表示以普通文本发送，改为html可以以HTML格式发送
    src = "qa_report@inke.cn"
    smtp_host = "mailrelay.inke.srv"  # smtp 地址
    msg["From"] = src  # 发件人
    msg["Subject"] = title  # 主题
    msg["To"] = ",".join(to)  # 收件人
    msg["Cc"] = ",".join(cc)  # 抄送人

    try:
        server = smtplib.SMTP(smtp_host, 25)
        server.sendmail(src, to+cc, msg.as_string())
    except Exception as e:
        "Failed Mail To [%s], err=[%s]" % (to, str(e))
        return False
    return True


def mailimg(title,to, cc,content,file_path):
    sender = 'qa_report@inke.cn'

    msgRoot = MIMEMultipart('related')
    msgRoot['From'] = sender
    msgRoot['To'] = ",".join(to)  # 收件人
    msgRoot['Cc'] = ",".join(cc)  # 抄送人
    msgRoot['Subject'] = title

    msgAlternative = MIMEMultipart('alternative')
    msgRoot.attach(msgAlternative)

    content = content

    msgAlternative.attach(MIMEText(content, 'html', 'utf-8'))

    # 指定图片为当前目录
    fp = open(file_path, 'rb')
    msgImage = MIMEImage(fp.read())
    fp.close()

    # 定义图片 ID，在 HTML 文本中引用
    msgImage.add_header('Content-ID', '<image1>')
    msgRoot.attach(msgImage)

    try:
        smtpObj = smtplib.SMTP('mailrelay.inke.srv')
        smtpObj.sendmail(sender, to+cc, msgRoot.as_string())
        return True
    except smtplib.SMTPException:
        return False


if __name__ == '__main__':
    pass
    #print(mailrelay('测试邮件',['chenzhibin@inke.cn'], ['fengsihua@inke.cn'], 'Hello!'))