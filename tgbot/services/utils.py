import phonenumbers
from phonenumbers import NumberParseException


def parse_phone_number(phone_number) -> str | None:
    """
    Parsing a phone number with an attempt to replace the first 8 with 7 and add 7 if it is not there, on error

    :param phone_number:
    :return: String phone number in E164 format or None if number is not vaild
    """
    phone_number = str(phone_number)
    if not phone_number.startswith('+'):
        phone_number = '+' + phone_number

    try:
        parsed_number = phonenumbers.parse(phone_number)
    except NumberParseException:
        phone_number = phone_number.replace('8', '7', 1)
        try:
            parsed_number = phonenumbers.parse(phone_number)
        except NumberParseException:
            return None

    if not phonenumbers.is_valid_number(parsed_number):
        phone_number = phone_number.replace('+', '+7')
        try:
            parsed_number = phonenumbers.parse(phone_number)
        except NumberParseException:
            return None

    if not phonenumbers.is_valid_number(parsed_number):
        return None

    return phonenumbers.format_number(parsed_number, phonenumbers.PhoneNumberFormat.E164)
