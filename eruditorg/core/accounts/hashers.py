# -*- coding: utf-8 -*-

import base64
import collections
import hashlib

from django.conf import settings
from django.contrib.auth.hashers import BasePasswordHasher
from django.contrib.auth.hashers import PBKDF2PasswordHasher
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_noop as _


class PBKDF2WrappedAbonnementsSHA1PasswordHasher(PBKDF2PasswordHasher):
    """ This hasher wraps existing 'abonnements' SHA1 passwords.

    This password hasher allow to store weak hashes from the 'abonnement' DB (SHA1) using the
    PBKDF2(AbonnementsSHA1(password)) algorithm.
    """
    algorithm = 'pbkdf2_wrapped_abonnements_sha1'

    def encode_sha1_hash(self, sha1_hash, salt, iterations=None):
        """ Encodes a SHA1-password that comes from the 'abonnement' DB. """
        return super(PBKDF2WrappedAbonnementsSHA1PasswordHasher, self).encode(
            sha1_hash, salt, iterations)

    def encode(self, password, salt, iterations=None, legacy_salt=None):
        """ Encodes a password using the Abonnements-SHA1 algorithm from the legacy system. """
        sha1_hash = self.sha1(password, legacy_salt)
        return self.encode_sha1_hash(sha1_hash, salt, iterations)

    def sha1(self, password, legacy_salt=None):
        """ Encodes using the crypt function from the legacy system. """
        if legacy_salt is None:
            legacy_salt = settings.INDIVIDUAL_SUBSCRIPTION_SALT
        to_sha = password.encode('utf-8') + legacy_salt.encode('utf-8')
        hashy = hashlib.sha1(to_sha).digest()
        sha1_hash = base64.b64encode(hashy + legacy_salt.encode('utf-8')).decode('utf-8')
        return sha1_hash


class DrupalPasswordHasher(BasePasswordHasher):
    """ Allows to authenticate users using Drupal 7 passwords.

    The passwords that are imported from a Drupal database should be prefixed with 'drupal$'.
    This hasher is inspired from the following snippet: https://djangosnippets.org/snippets/3030/
    """
    algorithm = 'drupal'

    _DRUPAL_HASH_LENGTH = 55
    _DRUPAL_HASH_COUNT = 15

    _digests = {
        '$S$': hashlib.sha512,
        '$H$': hashlib.md5,
        '$P$': hashlib.md5,
    }

    _itoa64 = './0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'

    def _get_settings(self, encoded):
        settings_bin = encoded[:12]
        count_log2 = self._itoa64.index(settings_bin[3])
        count = 1 << count_log2
        salt = settings_bin[4:12]
        return {'count': count, 'salt': salt, }

    def _drupal_b64(self, input):
        output = ''
        count = len(input)
        i = 0
        while True:
            value = input[i]
            i += 1
            output += self._itoa64[value & 0x3f]
            if i < count:
                value |= input[i] << 8
            output += self._itoa64[(value >> 6) & 0x3f]
            i += 1
            if i >= count:
                break
            if i < count:
                value |= input[i] << 16
            output += self._itoa64[(value >> 12) & 0x3f]
            i += 1
            if i >= count:
                break
            output += self._itoa64[(value >> 18) & 0x3f]
        return output

    def _apply_hash(self, password, digest, settings):
        password_hash = digest(settings['salt'].encode('utf-8') + password.encode('utf-8')).digest()
        for i in range(settings['count']):
            password_hash = digest(password_hash + password.encode('utf-8')).digest()
        return self._drupal_b64(password_hash)[:self._DRUPAL_HASH_LENGTH - 12]

    def salt(self):
        return get_random_string(8)

    def encode(self, password, salt):
        assert len(salt) == 8
        digest = '$S$'
        settings = {'count': 1 << self._DRUPAL_HASH_COUNT, 'salt': salt, }
        encoded_hash = self._apply_hash(password, self._digests[digest], settings)
        return self.algorithm + '$' + digest + self._itoa64[self._DRUPAL_HASH_COUNT] + salt \
            + encoded_hash

    def verify(self, password, encoded):
        encoded = encoded.split('$', 1)[1]
        if encoded[0] == 'U':
            encoded = encoded[1:]
            password = hashlib.md5(password.encode('utf-8')).hexdigest()
        digest = encoded[:3]
        assert digest in self._digests
        digest = self._digests[digest]
        settings = self._get_settings(encoded)

        encoded_hash = encoded[12:]
        password_hash = self._apply_hash(password, digest, settings)

        return password_hash == encoded_hash

    def safe_summary(self, encoded):
        encoded = encoded.split('$', 1)[1]
        settings = self._get_settings(encoded)
        return collections.OrderedDict([
            (_('algorithm'), self.algorithm),
            (_('iterations'), settings['count']),
            (_('salt'), settings['salt']),
            (_('hash'), encoded[12:]),
        ])

    def must_update(self, encoded):
        encoded = encoded.split('$', 1)[1]
        if encoded[0] == 'U':
            return True
        settings = self._get_settings(encoded)
        return settings['count'] < (1 << self._DRUPAL_HASH_COUNT)
