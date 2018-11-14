# Shopit's example project

Minimal settings example project for testing with some dummy data.
Usefull if you need help setting up your project.

---

## Installation

To start a new example project do the following:

```bash
python manage.py migrate
python manage.py loaddata fixtures/example.json
python manage.py runserver
```

After that's done, you can login as superuser with credentials:

* Email: ``admin@example.com``
* Username: ``admin``
* Password: ``admin``

## Documentation

For full documentation visit [ReadTheDocs](http://django-shopit.readthedocs.org).
