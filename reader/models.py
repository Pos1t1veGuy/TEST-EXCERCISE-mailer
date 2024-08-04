from django.db import models
from django.conf import settings


class IMAP_server(models.Model):
	url = models.CharField(max_length=255, unique=True)
	port = models.IntegerField(default=993)

class EmailAccount(models.Model):
	email = models.CharField(max_length=255, unique=True)
	password = models.CharField(max_length=255)
	server = models.ForeignKey(IMAP_server, related_name='accounts', on_delete=models.CASCADE)

	@property
	def name(self) -> str:
		return self.email.split('@')[0]


class EmailMessage(models.Model):
	id = models.CharField(max_length=255, unique=True, primary_key=True)
	sender = models.ForeignKey(EmailAccount, related_name='messages', on_delete=models.CASCADE)
	mailbox = models.CharField(max_length=255)
	From = models.CharField(max_length=255)
	To = models.CharField(max_length=255)
	subject = models.CharField(null=True, blank=True, max_length=255)
	date_sent = models.DateTimeField()
	date_received = models.DateTimeField()
	body = models.TextField(null=True, blank=True)

class EmailAttachment(models.Model):
	path = models.CharField(max_length=255)
	date_saved = models.DateTimeField(auto_now=True)
	email_message = models.ForeignKey(EmailMessage, related_name='attachments', on_delete=models.CASCADE)

	@property
	def name(self) -> str:
		return self.path.split('/')[-1]

	@property
	def url(self) -> str:
		return settings.ATTACHMENTS_URL + self.name


def msg_to_model(msg: 'Message', sender: 'EmailAccount') -> 'EmailMessage':
	msg_model = EmailMessage(
		id=msg.id, sender=sender, mailbox=msg.mailbox_name,
		From=msg.From, To=msg.To, subject=msg.subject,
		date_sent=msg.date_sent, date_received=msg.date_received,
		body=msg.body
	)
	msg_model.save()

	for filename in msg.save_attachments(settings.ATTACHMENTS_ROOT, name_format='{short_id}_{username}_{name}', format_kwargs={'username': sender.name}):
		EmailAttachment.objects.create(path=f'{settings.ATTACHMENTS_ROOT}/{filename}', email_message=msg_model)

	return msg_model