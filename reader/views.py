from django.shortcuts import render
from django.http import HttpResponse
from django.shortcuts import render
from django.views import View
from django.core.exceptions import ValidationError
from django.db import transaction
from django import forms

from imaplib import *
import socket

from .mailer import Mailer
from .models import EmailAccount, IMAP_server


class main_view(View):
	template = 'main.html'

	def get(self, request):
		return render(request, self.template, {'form': MailForm()})

	def post(self, request):
		form = MailForm(request.POST)
		if form.is_valid():
			return render(request, self.template, {'form': form, 'status': 'OK'})
		else:
			return render(request, self.template, {'form': form, 'status': 'ERROR'})


class MailForm(forms.Form):
	email = forms.CharField(label='Почта', max_length=254)
	password = forms.CharField(label='Пароль', max_length=254, widget=forms.PasswordInput)
	server = forms.CharField(label='IMAP Сервер', max_length=254)
	port = forms.IntegerField(label='Порт', initial=993)
	mailbox = forms.CharField(label='Папка', initial='inbox', max_length=254)
	range = forms.IntegerField(label='Диапазон от последнего сообщения до первого', 
		widget=forms.NumberInput(attrs={'min': -100_000, 'max': 100_000}),
		min_value=1,
		max_value=100_000,
		initial=0,
	)

	def clean(self):
		cleaned_data = super().clean()
		email = self.cleaned_data.get('email')
		password = self.cleaned_data.get('password')
		server = self.cleaned_data.get('server')
		port = self.cleaned_data.get('port')
		mailbox = self.cleaned_data.get('mailbox')
		scan_range = self.cleaned_data.get('range')

		try:
			imap = Mailer(email, password, server, port=port)
			box = imap[mailbox]
		except IMAP4.error as e:
			raise ValidationError(e)
		except socket.gaierror:
			raise ValidationError('Invalid server or port')

		with transaction.atomic():
			server, _ = IMAP_server.objects.get_or_create(url=str(server), port=int(port))
			EmailAccount.objects.get_or_create(email=str(email), password=str(password), server=server)
			
		return self.cleaned_data