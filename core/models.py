# core/models.py
"""
SQL Buddy Models - 所有15个表
基于Phase 4的GCP MySQL数据库
使用 managed=False 因为表已经存在
"""

from django.db import models
from django.utils import timezone


# ==================== User相关 (4个表) ====================

class User(models.Model):
    """用户表 - 超类"""
    user_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.CharField(unique=True, max_length=150)
    password = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        managed = False
        db_table = 'User'
    
    def __str__(self):
        return f"{self.name} ({self.email})"
    
    def get_role(self):
        """获取用户角色"""
        if hasattr(self, 'student'):
            return 'Student'
        elif hasattr(self, 'mentor'):
            return 'Mentor'
        elif hasattr(self, 'admin'):
            return 'Admin'
        return 'Unknown'


class Student(models.Model):
    """学生表"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='user_id',
        related_name='student'
    )
    enrollment_date = models.DateField(auto_now_add=True)
    total_problems_attempted = models.IntegerField(default=0)
    
    class Meta:
        managed = False
        db_table = 'Student'
    
    def __str__(self):
        return f"Student: {self.user.name}"


class Mentor(models.Model):
    """导师表"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='user_id',
        related_name='mentor'
    )
    expertise_area = models.CharField(max_length=100, blank=True, null=True)
    problems_created = models.IntegerField(default=0)
    
    class Meta:
        managed = False
        db_table = 'Mentor'
    
    def __str__(self):
        return f"Mentor: {self.user.name}"


class Admin(models.Model):
    """管理员表"""
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        primary_key=True,
        db_column='user_id',
        related_name='admin'
    )
    admin_level = models.CharField(max_length=8, default='Standard')
    
    class Meta:
        managed = False
        db_table = 'Admin'
    
    def __str__(self):
        return f"Admin: {self.user.name}"


# ==================== 问题相关 (4个表) ====================

class Topic(models.Model):
    """主题表"""
    topic_name = models.CharField(primary_key=True, max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        managed = False
        db_table = 'Topic'
    
    def __str__(self):
        return self.topic_name


class Scenario(models.Model):
    """学习场景表"""
    scenario_no = models.AutoField(primary_key=True)
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        db_column='student_id'
    )
    scenario_description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        managed = False
        db_table = 'Scenario'
    
    def __str__(self):
        return f"Scenario #{self.scenario_no}"


class Problem(models.Model):
    """问题表"""
    problem_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        Mentor,
        on_delete=models.CASCADE,
        db_column='user_id'
    )
    correct_answer = models.TextField()
    create_time = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=200)
    difficulty = models.CharField(max_length=6)
    scenario = models.ForeignKey(
        Scenario,
        on_delete=models.SET_NULL,
        db_column='scenario_no',
        null=True,
        blank=True
    )
    description = models.TextField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'Problem'
    
    def __str__(self):
        return f"{self.title} ({self.difficulty})"


class Attempt(models.Model):
    """尝试记录表 - 弱实体"""
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        db_column='student_id'
    )
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        db_column='problem_id'
    )
    attempt_no = models.IntegerField()
    mentor = models.ForeignKey(
        Mentor,
        on_delete=models.SET_NULL,
        db_column='mentor_id',
        null=True,
        blank=True
    )
    score = models.DecimalField(max_digits=5, decimal_places=2)
    submit_time = models.DateTimeField(auto_now_add=True)
    feedback = models.TextField(blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'Attempt'
        unique_together = (('student', 'problem', 'attempt_no'),)
    
    def __str__(self):
        return f"Attempt #{self.attempt_no}"


class HaveTopic(models.Model):
    """Problem-Topic关系表"""
    problem = models.ForeignKey(
        Problem,
        on_delete=models.CASCADE,
        db_column='problem_id'
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        db_column='topic_name',
        to_field='topic_name'
    )
    
    class Meta:
        managed = False
        db_table = 'Have_topic'
        unique_together = (('problem', 'topic'),)


# ==================== Resource相关 (3个表) ====================

class Resource(models.Model):
    """学习资源表"""
    resource_id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        Mentor,
        on_delete=models.CASCADE,
        db_column='user_id'
    )
    title = models.CharField(max_length=200)
    res_type = models.CharField(max_length=13)
    uploaded_time = models.DateTimeField(auto_now_add=True)
    resource_url = models.CharField(max_length=500, blank=True, null=True)
    
    class Meta:
        managed = False
        db_table = 'Resource'
    
    def __str__(self):
        return f"{self.title} ({self.res_type})"


class ResourceTopic(models.Model):
    """Resource-Topic关系表"""
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        db_column='resource_id'
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        db_column='topic_name',
        to_field='topic_name'
    )
    
    class Meta:
        managed = False
        db_table = 'ResourceTopic'
        unique_together = (('resource', 'topic'),)


class Access(models.Model):
    """Student访问Resource记录"""
    resource = models.ForeignKey(
        Resource,
        on_delete=models.CASCADE,
        db_column='resource_id'
    )
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        db_column='student_id'
    )
    access_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        managed = False
        db_table = 'Access'
        unique_together = (('resource', 'student'),)


# ==================== Notification相关 (3个表) ====================

class Notification(models.Model):
    """通知表"""
    noti_id = models.AutoField(primary_key=True)
    send_time = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        managed = False
        db_table = 'Notification'
    
    def __str__(self):
        return f"Notification #{self.noti_id}"


class Send(models.Model):
    """User发送Notification"""
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='sender_id'
    )
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        db_column='noti_id'
    )
    
    class Meta:
        managed = False
        db_table = 'Send'
        unique_together = (('sender', 'notification'),)


class Receive(models.Model):
    """User接收Notification"""
    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column='receiver_id'
    )
    notification = models.ForeignKey(
        Notification,
        on_delete=models.CASCADE,
        db_column='noti_id'
    )
    
    class Meta:
        managed = False
        db_table = 'Receive'
        unique_together = (('receiver', 'notification'),)