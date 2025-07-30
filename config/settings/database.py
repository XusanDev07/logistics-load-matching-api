import os

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'logistics_load',
        'USER': 'logist_user',
        'PASSWORD': '12345',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
