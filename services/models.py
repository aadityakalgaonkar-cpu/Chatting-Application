# Create your models here.
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE
    )

    profile_picture = models.ImageField(
        upload_to="profile_pictures/",
        default="default.png"
    )

    bio = models.CharField(
        max_length=200,
        blank=True
    )

    phone = models.CharField(
        max_length=15,
        blank=True
    )

    is_online = models.BooleanField(
        default=False
    )

    last_seen = models.DateTimeField(
        auto_now=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.user.username

class Conversation(models.Model):

    is_group = models.BooleanField(
        default=False
    )

    group_name = models.CharField(
        max_length=100,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return str(self.id)

class Message(models.Model):

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    message = models.TextField()

    file = models.FileField(
        upload_to="chat_files/",
        blank=True,
        null=True
    )

    image = models.ImageField(
        upload_to="chat_images/",
        blank=True,
        null=True
    )

    timestamp = models.DateTimeField(
        auto_now_add=True
    )

    is_seen = models.BooleanField(
        default=False
    )

    def __str__(self):
        return self.sender.username

class ChatBackup(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    backup_file = models.FileField(
        upload_to="backups/"
    )

    backup_date = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.user.username

class ConversationParticipant(models.Model):

    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE
    )

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    joined_at = models.DateTimeField(
        auto_now_add=True
    )


    class Meta:
        unique_together = ("conversation", "user")


    def __str__(self):
        return self.user.username
