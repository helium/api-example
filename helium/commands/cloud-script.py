import dpath.util as dpath
import urlparse
import requests
import click
import helium
import util
import timeseries as ts

pass_service=click.make_pass_decorator(helium.Service)

@click.group()
def cli():
    """Operations on cloud-scripts
    """
    pass

def _tabulate(result):
    def _map_script_filenames(json):
        files = dpath.get(json, 'meta/scripts')
        return ','.join(_extract_script_filenames(files))

    util.output(util.tabulate(result, [
        ('id', 'id'),
        ('state', 'attributes/state'),
        ('name', 'attributes/name'),
        ('files', _map_script_filenames),
        ('error', 'attributes/error/error')
    ]))


def _extract_script_filenames(files):
    return [urlparse.urlsplit(url).path.split('/')[-1] for url in files]


@cli.command()
@pass_service
def list(service):
    """List all known cloud-scripts.

    Lists all cloud-scripts for the organization.
    """
    _tabulate(service.get_cloud_scripts().get('data'))

@cli.command()
@click.argument('script')
@click.option('--name',
              help="the new name for the script")
@pass_service
def start(service, script):
    """Starts a given cloud-script.

    Starts the SCRIPT with the given id.
    """
    _tabulate([service.update_cloud_script(script, name=name, start=True).get('data')])

@cli.command()
@click.argument('script')
@click.option('--name',
              help="the new name for the script")
@pass_service
def stop(service, script, name):
    """Stop a given cloud-script.

    Stops the SCRIPT with the given id.
    """
    _tabulate([service.update_cloud_script(script, name=name, start=False).get('data')])


@cli.command()
@click.argument('script')
@pass_service
def delete(service, script):
    """Delete a given cloud-script.

    Deletes the cloud-SCRIPT with the given id.
    """
    result = service.delete_cloud_script(script)
    click.echo("Deleted" if result.status_code == 204 else result)


@cli.command()
@click.argument('script')
@ts.options()
@pass_service
def timeseries(service, script, **kwargs):
    """List readings for a cloud-script.

    Lists one page of readings for a given SCRIPT.
    Readings can be filtered by PORT and by START and END date. Dates are given
    in ISO-8601 and may be one of the following forms:

    \b
    * YYYY-MM-DD - Example: 2016-05-05
    * YYYY-MM-DDTHH:MM:SSZ - Example: 2016-04-07T19:12:06Z

    """
    data = service.get_cloud_script_timeseries(script, **kwargs).get('data')
    ts.tabulate(data)


@cli.command()
@click.argument('script')
@click.argument('file')
@pass_service
def show(service, script, file):
    """Gets a script file from a given cloud-script.

    Fetches a FILE from a given cloud-SCRIPT.
    """
    json = service.get_cloud_script(script).get('data')
    file_urls = [f.encode('utf-8') for f in dpath.get(json, 'meta/scripts')]
    names = dict(zip(_extract_script_filenames(file_urls), file_urls))
    file_url = names[opts.file]
    click.echo(requests.get(file_url).text())


@cli.command()
@click.argument('file', nargs=-1)
@click.option('--main', type=click.Path(exists=True),
              help="The main file for the script")
@pass_service
def deploy(service, file, main):
    """Deploy  a cloud-script.

    Submits a deploy request of one ore more FILEs.

    If the --main option is specified the given file is used as the `user.lua`,
    i.e. the main user script for the deployment. The file may  be part of
    the list of files given to make it easier to specify wildcards

    Note: One of the given files _must_ be called user.lua if the --main option is not given.
    This file will be considered the primary script for the deploy.
    """
    deploy=service.deploy_cloud_script(file, main=main).get('data')
    _tabulate([deploy])


@cli.command()
@click.argument('script')
@pass_service
def status(service, script):
    """Displays current status information for a script.

    Display status information a given SCRIPT. If the script is in an error
    condition the error details are displayed.
    """
    data = service.get_cloud_script(script).get('data')
    click.echo('Status: ' + dpath.get(data, "attributes/state"))
    error = dpath.get(data, "attributes/error")
    if error:
        click.echo('Error: ' + error.get('details'))