"""
CLI Command for Validating a SAM Template
"""
import os

import boto3
import botocore

import click
from samtranslator.translator.managed_policy_translator import ManagedPolicyLoader


from samcli.cli.main import pass_context, common_options as cli_framework_options
from samcli.commands.local.cli_common.options import template_common_option as template_option, profile_common_option as profile_option
from samcli.commands.local.cli_common.user_exceptions import InvalidSamTemplateException, SamTemplateNotFoundException, InvalidProfileException
from samcli.yamlhelper import yaml_parse
from .lib.exceptions import InvalidSamDocumentException
from .lib.sam_template_validator import SamTemplateValidator


@click.command("validate",
               short_help="Validate an AWS SAM template.")
@profile_option
@template_option
@cli_framework_options
@pass_context
def cli(ctx, template, profile):

    # All logic must be implemented in the ``do_cli`` method. This helps with easy unit testing

    do_cli(ctx, template, profile)  # pragma: no cover


def do_cli(ctx, template, profile=None):
    """
    Implementation of the ``cli`` method, just separated out for unit testing purposes
    """

    sam_template = _read_sam_file(template)
    iam_client = _get_boto_client(profile)
    validator = SamTemplateValidator(sam_template, ManagedPolicyLoader(iam_client))

    try:
        validator.is_valid()
    except InvalidSamDocumentException as e:
        click.secho("Template provided at '{}' was invalid SAM Template.".format(template), bg='red')
        raise InvalidSamTemplateException(str(e))

    click.secho("{} is a valid SAM Template".format(template), fg='green')


def _get_boto_client(profile):
    # If a profile is passed, instantiate the boto3 client from the session.
    if profile:
        try:
            session = boto3.Session(profile_name=profile)
            return session.client('iam')
        except botocore.exceptions.ProfileNotFound as e:
            click.secho("Profile '{}' was not found. Check your credential file.".format(profile), bg='red')
            raise InvalidProfileException(str(e))

    return boto3.client('iam')


def _read_sam_file(template):
    """
    Reads the file (json and yaml supported) provided and returns the dictionary representation of the file.

    :param str template: Path to the template file
    :return dict: Dictionary representing the SAM Template
    :raises: SamTemplateNotFoundException when the template file does not exist
    """
    if not os.path.exists(template):
        click.secho("SAM Template Not Found", bg='red')
        raise SamTemplateNotFoundException("Template at {} is not found".format(template))

    with click.open_file(template, 'r') as sam_template:
        sam_template = yaml_parse(sam_template.read())

    return sam_template
