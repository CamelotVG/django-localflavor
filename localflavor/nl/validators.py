# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
import warnings

from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.utils.deconstruct import deconstructible
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _

from localflavor.deprecation import RemovedInLocalflavor20Warning


class NLZipCodeFieldValidator(RegexValidator):
    """
    Validation for Dutch zip codes.

    .. versionadded:: 1.3
    """

    error_message = _('Enter a valid zip code.')

    def __init__(self):
        super(NLZipCodeFieldValidator, self).__init__(regex='^\d{4} ?[A-Z]{2}$',
                                                      message=self.error_message)

    def __call__(self, value):
        super(NLZipCodeFieldValidator, self).__call__(value)

        if int(value[:4]) < 1000:
            raise ValidationError(self.error_message)


class NLBSNFieldValidator(RegexValidator):
    """
    Validation for Dutch social security numbers (BSN).

    .. versionadded:: 1.6
    """

    error_message = _('Enter a valid BSN.')

    def __init__(self):
        super(NLBSNFieldValidator, self).__init__(regex='^\d{9}$', message=self.error_message)

    def bsn_checksum_ok(self, value):
        checksum = 0
        for i in range(9, 1, -1):
            checksum += int(value[9 - i]) * i
        checksum -= int(value[-1])

        return checksum % 11 == 0

    def __call__(self, value):
        super(NLBSNFieldValidator, self).__call__(value)

        if int(value) == 0:
            raise ValidationError(self.error_message)

        if not self.bsn_checksum_ok(value):
            raise ValidationError(self.error_message)


class NLSoFiNumberFieldValidator(NLBSNFieldValidator):
    """
    Validation for Dutch SoFinummers.

    .. versionadded:: 1.3
    .. deprecated:: 1.6
        Use `NLBSNFieldValidator` instead.
    """
    error_message = _('Enter a valid SoFi number.')

    def __init__(self):
        warnings.warn('NLSoFiNumberFieldValidator is deprecated. Please use NLBSNFieldValidator instead.',
                      RemovedInLocalflavor20Warning)
        super(NLSoFiNumberFieldValidator, self).__init__()

    def sofi_checksum_ok(self, value):
        return self.bsn_checksum_ok(value)


@deconstructible
class NLPhoneNumberFieldValidator(object):
    """
    Validation for Dutch phone numbers.

    .. versionadded:: 1.3
    .. deprecated:: 1.6.1
        Use the django-phonenumber-field_ library instead.

    .. _django-phonenumber-field: https://github.com/stefanfoulis/django-phonenumber-field
    """

    def __init__(self):
        warnings.warn('NLPhoneNumberFieldValidator is deprecated in favor of the django-phonenumber-field library.',
                      RemovedInLocalflavor20Warning)
        super(NLPhoneNumberFieldValidator, self).__init__()

    def __eq__(self, other):
        # The is no outside modification of properties so this should always be true by default.
        return True

    def __call__(self, value):
        phone_nr = re.sub('[\-\s\(\)]', '', force_text(value))
        numeric_re = re.compile('^\d+$')

        if len(phone_nr) == 10 and numeric_re.search(phone_nr):
            return

        if phone_nr[:3] == '+31' and len(phone_nr) == 12 and numeric_re.search(phone_nr[3:]):
            return

        raise ValidationError(_('Enter a valid phone number.'))


class NLBankAccountNumberFieldValidator(RegexValidator):
    """
    Validation for Dutch bank accounts.

    Validation references:
    http://www.mobilefish.com/services/elfproef/elfproef.php
    http://www.credit-card.be/BankAccount/ValidationRules.htm#NL_Validation

    .. versionadded:: 1.1
    .. deprecated:: 1.6.1

    NLBankAccountNumberFieldValidator is deprecated. Non-IBAN bank account numbers are no longer used in the
    Netherlands. Use the IBAN field and validator instead.
    """

    default_error_messages = {
        'invalid': _('Enter a valid bank account number.'),
        'wrong_length': _('Bank account numbers have 1 - 7, 9 or 10 digits.'),
    }

    def __init__(self, regex=None, message=None, code=None):
        warnings.warn('NLBankAccountNumberFieldValidator is deprecated. Non-IBAN bank account numbers are no longer '
                      'used in the Netherlands. Use the IBAN field and validator instead.',
                      RemovedInLocalflavor20Warning)
        super(NLBankAccountNumberFieldValidator, self).__init__(regex='^[0-9]+$',
                                                                message=self.default_error_messages['invalid'])
        self.no_leading_zeros_regex = re.compile('[1-9]+')

    def __call__(self, value):
        super(NLBankAccountNumberFieldValidator, self).__call__(value)

        # Need to check for values over the field's max length before the zero are stripped.
        # This check is needed to allow this validator to be used without Django's MaxLengthValidator.
        if len(value) > 10:
            raise ValidationError(self.default_error_messages['wrong_length'])

        # Strip the leading zeros.
        m = re.search(self.no_leading_zeros_regex, value)
        if not m:
            raise ValidationError(self.default_error_messages['invalid'])
        value = value[m.start():]

        if len(value) != 9 and len(value) != 10 and not 1 <= len(value) <= 7:
            raise ValidationError(self.default_error_messages['wrong_length'])

        # Perform the eleven test validation on non-PostBank numbers.
        if len(value) == 9 or len(value) == 10:
            if len(value) == 9:
                value = "0" + value

            eleven_test_sum = sum([int(a) * b for a, b in zip(value, range(1, 11))])
            if eleven_test_sum % 11 != 0:
                raise ValidationError(self.default_error_messages['invalid'])
