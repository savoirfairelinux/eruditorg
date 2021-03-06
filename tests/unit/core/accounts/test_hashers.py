# -*- coding: utf-8 -*-

import hashlib

from django.contrib.auth.models import User

from base.test.testcases import EruditClientTestCase
from core.accounts.hashers import DrupalPasswordHasher
from core.accounts.hashers import PBKDF2WrappedAbonnementsSHA1PasswordHasher


class TestPBKDF2WrappedAbonnementsSHA1PasswordHasher(EruditClientTestCase):
    def test_can_generate_usable_passwords_for_users(self):
        # Setup
        hasher = PBKDF2WrappedAbonnementsSHA1PasswordHasher()
        legacy_password = hasher.sha1('dummypassword')
        user = User.objects.create_user(username='dummy', email='dummy@xyz.com', password='void')
        user.password = hasher.encode_sha1_hash(legacy_password, hasher.salt())
        user.save()
        # Run & check
        assert self.client.login(username='dummy', password='dummypassword')

    def test_will_not_be_used_if_the_password_of_the_user_is_updated(self):
        # Setup
        hasher = PBKDF2WrappedAbonnementsSHA1PasswordHasher()
        legacy_password = hasher.sha1('dummypassword')
        user = User.objects.create_user(username='dummy', email='dummy@xyz.com', password='void')
        user.password = hasher.encode_sha1_hash(legacy_password, hasher.salt())
        user.save()
        user.set_password('newdummypassword')
        user.save()
        # Run & check
        assert self.client.login(username='dummy', password='newdummypassword')
        algorithm, _, _, _ = user.password.split('$')
        assert algorithm == 'pbkdf2_sha256'


class TestDrupalPasswordHasher(EruditClientTestCase):
    def test_can_generate_usable_passwords_for_users_using_sha512(self):
        # Setup
        hasher = DrupalPasswordHasher()
        user = User.objects.create_user(username='dummy', email='dummy@xyz.com', password='void')
        user.password = hasher.encode('dummypassword', hasher.salt())
        user.save()
        # Run & check
        assert self.client.login(username='dummy', password='dummypassword')

    def test_can_work_with_drupal_passwords_using_md5(self):
        # Setup
        hasher = DrupalPasswordHasher()
        user = User.objects.create_user(username='dummy', email='dummy@xyz.com', password='void')
        digest = '$P$'
        salt = hasher.salt()
        settings = {
            'count': 1 << hasher._DRUPAL_HASH_COUNT,
            'salt': salt
        }
        encoded_hash = hasher._apply_hash('dummypassword', hasher._digests[digest], settings)
        user.password = 'drupal$$P$' + hasher._itoa64[hasher._DRUPAL_HASH_COUNT] + salt \
            + encoded_hash
        user.save()
        # Run & check
        assert self.client.login(username='dummy', password='dummypassword')

    def test_can_work_with_drupal_passwords_using_md5_alternative(self):
        # Setup
        hasher = DrupalPasswordHasher()
        user = User.objects.create_user(username='dummy', email='dummy@xyz.com', password='void')
        digest = '$P$'
        salt = hasher.salt()
        settings = {
            'count': 1 << hasher._DRUPAL_HASH_COUNT,
            'salt': salt
        }
        encoded_hash = hasher._apply_hash('dummypassword', hasher._digests[digest], settings)
        user.password = 'drupal$$H$' + hasher._itoa64[hasher._DRUPAL_HASH_COUNT] + salt \
            + encoded_hash
        user.save()
        # Run & check
        assert self.client.login(username='dummy', password='dummypassword')

    def test_cannot_work_with_drupal_passwords_that_must_be_updated(self):
        # Setup
        hasher = DrupalPasswordHasher()
        user = User.objects.create_user(username='dummy', email='dummy@xyz.com', password='void')
        digest = '$P$'
        salt = hasher.salt()
        settings = {
            'count': 1 << hasher._DRUPAL_HASH_COUNT,
            'salt': salt
        }
        encoded_hash = hasher._apply_hash('dummypassword', hasher._digests[digest], settings)
        user.password = 'drupal$U$P$' + hasher._itoa64[hasher._DRUPAL_HASH_COUNT] + salt \
            + encoded_hash
        user.save()
        # Run & check
        assert not self.client.login(username='dummy', password='dummypassword')

    def test_will_not_be_used_if_the_password_of_the_user_is_updated(self):
        # Setup
        hasher = DrupalPasswordHasher()
        user = User.objects.create_user(username='dummy', email='dummy@xyz.com', password='void')
        user.password = hasher.encode('dummypassword', hasher.salt())
        user.save()
        user.set_password('newdummypassword')
        user.save()
        # Run & check
        assert self.client.login(username='dummy', password='newdummypassword')
        algorithm, _, _, _ = user.password.split('$')
        assert algorithm == 'pbkdf2_sha256'

    def test_safe_summary(self):
        # Setup
        hasher = DrupalPasswordHasher()
        password = 'dummypassword'
        encoded = hasher.encode(password, hasher.salt())
        # Run & check
        summary_dict = hasher.safe_summary(encoded)
        assert summary_dict['algorithm'] == 'drupal'
        assert summary_dict['iterations'] > 0
        assert len(summary_dict['salt']) == 8
        assert len(summary_dict['hash']) == hasher._DRUPAL_HASH_LENGTH - 12

    def test_must_update(self):
        hasher = DrupalPasswordHasher()
        password = 'dummypassword'
        hash = hashlib.md5(password.encode('utf-8')).hexdigest()
        encoded = 'drupal$U$H$' + hash
        assert hasher.must_update(encoded)
