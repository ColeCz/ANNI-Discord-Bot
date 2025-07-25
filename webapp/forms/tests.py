from django.test import TestCase

# Basic tests for demonstration
# Tests tailored to your webapp
from django.urls import reverse
from . import utils

class ViewTests(TestCase):
    def test_home_view_renders(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "forms/home.html")

    def test_form_view_renders(self):
        response = self.client.get(reverse('form'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "forms/form.html")

    def test_about_view_renders(self):
        response = self.client.get(reverse('about'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "forms/about.html")

class UtilsTests(TestCase):
    def test_connect_db_exists(self):
        self.assertTrue(callable(utils.connect_db))

    def test_execute_query_exists(self):
        self.assertTrue(callable(utils.execute_query))
