import json
import os
from datetime import datetime, timedelta

from azure.communication.sms import SmsClient
from flask import current_app as app
from flask import make_response
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from xkcdpass import xkcd_password as xp

from app import status
from app.services import logger


# send email via sendgrid template
def send_email(email, token, template_id, recipient, seed=None):
    # Build the invitation email and submit the request to SendGrid
    logger.info("Sending email through sendgrid to recipient:" + email)
    message = Mail(
        from_email=app.config["SENDGRID_FROM_ADDRESS"],
        to_emails=email,
    )
    expire_date = datetime.today() + timedelta(
        days=int(app.config["TTLD_GENERATION_TO_CONSENT"])
    )
    date_time = expire_date.strftime("%m-%d-%Y")

    dict = {
        "coupon": token,
        "expireDate": date_time,
        "url": app.config["REACT_APP_UI_ROOT"],
        "user": recipient,
    }
    if seed:
        dict["seed"] = seed
    message.dynamic_template_data = dict
    message.template_id = template_id
    sendgrid_client = SendGridAPIClient(app.config["SENDGRID_API_KEY"])
    sendgrid_response = sendgrid_client.send(message)

    return sendgrid_response.status_code


# send SMS text message via AWS Pinpoint
def send_sms_txt(phone_number, coupon):
    message = generate_sms_message(coupon)
    client = SmsClient.from_connection_string(app.config["SMS_CONNECTION_STRING"])
    to_number = "+1" + phone_number.replace("-", "")
    responses = client.send(
        from_=app.config["SMS_PHONE_NUMBER"],
        to=to_number,
        message=message,
    )
    for response in responses:
        if response.successful:
            logger.info(f"SMS message successfully sent to {to_number}")
        else:
            logger.error(
                f"Failed to send SMS message to {to_number}: {response.error_message}"
            )

    # only expect 1:1 sms message
    return response.http_status_code


# generate message for sending by SMS
def generate_sms_message(coupon):
    message = (
        f"Please click to join Snowball Study: {app.config['REACT_APP_UI_ROOT']}/redeem?coupon="
        + coupon
        + " You will be compensated by the study team. Thank you!"
    )

    return message


def generate_coupon():
    """
    Generate the coupon
    :return: 4 words coupon
    """
    # """"""
    word_file = xp.locate_wordfile()
    my_words = xp.generate_wordlist(wordfile=word_file, min_length=4, max_length=5)
    coupon = xp.generate_xkcdpassword(my_words, numwords=4)
    coupon = "-".join(coupon.title().split())

    return coupon


def current_time():
    now = datetime.now()
    # dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

    return now


def response_with_status_code(
    msg, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, data=None
):
    resp = {"reason": msg}
    if data:
        resp["records"] = data
        resp["result"] = len(data)
    if status_code != status.HTTP_200_OK:
        resp["result"] = 0
        logger.error(resp)
    response = make_response(resp)
    response.status_code = status_code

    return response


def unauthorized_response():
    logger.info("Current user does not have permission to access this information.")
    resp = make_response(app.config["UNAUTHORIZED_MESSAGE"])
    resp.status_code = status.HTTP_403_FORBIDDEN
    return resp


def get_access_role(net_id):
    with open(
        os.path.join(os.path.dirname(__file__), "", "rbac_config.json")
    ) as json_file:
        access_roles = json.load(json_file)

        if access_roles.get(net_id):
            return access_roles.get(net_id).get("role")
        else:
            logger.warning("This netId doesn't exist on access roles list.")
            return None


def count_list_of_lists(input_lists):
    count = 0
    for listElem in input_lists:
        if type(listElem) is list:
            count += len(listElem)
        else:
            count += 1
    return count


def parse_age_group(age_group):
    age_group = age_group.split("-")
    return {"$gte": int(age_group[0]), "$lte": int(age_group[1])}


def parse_date_range(date_range):
    return {"$gte": (current_time() - timedelta(int(date_range)))}


def record_id_str(record_id):
    return str(record_id).zfill(8)


def contact_id_str(contact_id):
    return str(contact_id).zfill(3)
