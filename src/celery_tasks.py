from celery import Celery
from src.mail import mail, create_message
from asgiref.sync import async_to_sync # for support for cleery async task

c_app = Celery()

c_app.config_from_object("src.config")


@c_app.task()
def send_email(recipients: list[str], subject: str, body: str):

    message = create_message(recipients=recipients, subject=subject, body=body)

    # since celery is a synchronous fucntion we need
    # to convert the sync code to async function to be able to
    # run in a sync task
    async_to_sync(mail.send_message)(message)
    print("Email sent")