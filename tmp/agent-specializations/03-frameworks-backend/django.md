---
name: django
type: framework
priority: 2
token_estimate: 500
compatible_with: [developer, senior_software_engineer]
requires: [python]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# Django Engineering Expertise

## Specialist Profile
Django specialist building robust web applications. Expert in ORM, Django REST Framework, and the Django ecosystem.

## Implementation Guidelines

### Models

```python
from django.db import models
from django.utils import timezone
import uuid

class User(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=100)
    status = models.CharField(
        max_length=20,
        choices=[('active', 'Active'), ('inactive', 'Inactive')],
        default='active',
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['status', 'created_at']),
        ]

    def __str__(self):
        return self.email
```

### Django REST Framework

```python
from rest_framework import serializers, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'display_name', 'status', 'created_at']
        read_only_fields = ['id', 'created_at']

class CreateUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'display_name']

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

    def get_serializer_class(self):
        if self.action == 'create':
            return CreateUserSerializer
        return UserSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.query_params.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        user = self.get_object()
        user.status = 'active'
        user.save(update_fields=['status', 'updated_at'])
        return Response(UserSerializer(user).data)
```

### QuerySet Optimization

```python
# Avoid N+1 queries
users = User.objects.select_related('profile').prefetch_related('orders')

# Only fetch needed fields
users = User.objects.only('id', 'email', 'display_name')

# Aggregate
from django.db.models import Count, Sum
stats = User.objects.aggregate(
    total=Count('id'),
    active=Count('id', filter=models.Q(status='active')),
)

# Bulk operations
User.objects.filter(last_login__lt=threshold).update(status='inactive')
```

### Signals

```python
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=User)
def user_created(sender, instance, created, **kwargs):
    if created:
        send_welcome_email.delay(instance.id)
```

### Migrations Best Practices

```python
# Always include reverse migration
def forwards(apps, schema_editor):
    User = apps.get_model('users', 'User')
    User.objects.filter(status='').update(status='active')

def backwards(apps, schema_editor):
    pass  # Intentionally do nothing

class Migration(migrations.Migration):
    operations = [
        migrations.RunPython(forwards, backwards),
    ]
```

## Patterns to Avoid
- ❌ Fat views (move logic to services/models)
- ❌ N+1 queries (use select_related/prefetch)
- ❌ Logic in serializers (use services)
- ❌ Unindexed query fields

## Verification Checklist
- [ ] Proper model indexes
- [ ] QuerySet optimization
- [ ] DRF serializers for validation
- [ ] Migrations are reversible
- [ ] Tests use pytest-django
