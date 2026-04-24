from apps.users.models import User

u = User.objects.filter(username='admin').first()
if u:
    u.set_password('admin123')
    u.save()
    print('Password reset successfully!')
else:
    print('Admin user not found')
