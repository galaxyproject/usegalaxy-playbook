"""
A script to automate installation of tool repositories from a Galaxy Tool Shed
into an instance of Galaxy.

Galaxy instance details and the installed tools need to be provided in YAML
format in a separate file; see ``tool_list.yaml.sample`` for a sample of
such file.

When installing tools, this script expects any `tool_panel_section_id` provided
in the input file to already exist on the target Galaxy instance. If the section
does not exist, the tool will be installed outside any section. See
`shed_tool_conf.xml.sample` in this directory for a sample of such file. Before
running this script to install the tools, make sure to place such file into
Galaxy's configuration directory and set Galaxy configuration option
`tool_config_file` to include it.

Usage:

    python install_tool_shed_tools.py [-h]

Required libraries:
    bioblend, pyyaml
"""
import datetime as dt
import logging
import time
import yaml
from optparse import OptionParser

from bioblend.galaxy import GalaxyInstance
from bioblend.galaxy.toolshed import ToolShedClient
from bioblend.toolshed import ToolShedInstance
from bioblend.galaxy.client import ConnectionError

# Omit (most of the) logging by external libraries
logging.getLogger('bioblend').setLevel(logging.ERROR)
logging.getLogger('requests').setLevel(logging.ERROR)
logging.captureWarnings(True)  # Capture HTTPS warngings from urllib3


class ProgressConsoleHandler(logging.StreamHandler):
    """
    A handler class which allows the cursor to stay on
    one line for selected messages
    """
    on_same_line = False

    def emit(self, record):
        try:
            msg = self.format(record)
            stream = self.stream
            same_line = hasattr(record, 'same_line')
            if self.on_same_line and not same_line:
                stream.write('\r\n')
            stream.write(msg)
            if same_line:
                stream.write('.')
                self.on_same_line = True
            else:
                stream.write('\r\n')
                self.on_same_line = False
            self.flush()
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            self.handleError(record)


def _setup_global_logger():
    formatter = logging.Formatter('%(asctime)s %(levelname)-5s - %(message)s')
    progress = ProgressConsoleHandler()
    file_handler = logging.FileHandler('/tmp/galaxy_tool_install.log')
    console = logging.StreamHandler()
    console.setFormatter(formatter)

    logger = logging.getLogger('test')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(progress)
    logger.addHandler(file_handler)
    return logger


def load_input_file(tool_list_file='tool_list.yaml'):
    """
    Load YAML from the `tool_list_file` and return a dict with the content.
    """
    with open(tool_list_file, 'r') as f:
        tl = yaml.load(f)
    return tl


def galaxy_instance(url=None, api_key=None):
    """
    Get an instance of the `GalaxyInstance` object. If the arguments are not
    provided, load the default values using `load_input_file` method.
    """
    if not (url and api_key):
        tl = load_input_file()
        url = tl['galaxy_instance']
        api_key = tl['api_key']
    return GalaxyInstance(url, api_key)


def tool_shed_client(gi=None):
    """
    Get an instance of the `ToolShedClient` on a given Galaxy instance. If no
    value is provided for the `galaxy_instance`, use the default provided via
    `load_input_file`.
    """
    if not gi:
        gi = galaxy_instance()
    return ToolShedClient(gi)


def the_same_tool(tool_1_info, tool_2_info):
    """
    Given two dicts containing info about tools, determine if they are the same
    tool.

    Each of the dicts must have the following keys: `name`, `owner`, and
    (either `tool_shed` or `tool_shed_url`).
    """
    t1ts = tool_1_info.get('tool_shed', tool_1_info.get('tool_shed_url', None))
    t2ts = tool_2_info.get('tool_shed', tool_2_info.get('tool_shed_url', None))

    if tool_1_info.get('name') == tool_2_info.get('name') and \
       tool_1_info.get('owner') == tool_2_info.get('owner') and \
       (t1ts in t2ts or t2ts in t1ts):
        return True
    return False


def installed_revisions(tsc=None):
    """
    Return a list of tool revisions installed on the Galaxy instance via the Tool
    Shed client `tsc`. If the `tsc` is not specified, use the default one by
    calling `tool_shed_client` method.

    :rtype: list of dicts
    :return: Each dict in the returned list will have the following keys:
             `name`, `owner`, `tool_shed`, `revision`, and `latest` (the value
             for this key will be `True` if the installed revision is the
             `latest_installable_revision`).
    """
    if not tsc:
        tsc = tool_shed_client()
    installed_revisions_list = []
    itl = tsc.get_repositories()
    for it in itl:
        latest = None
        if it.get('tool_shed_status', None):
            latest = it['tool_shed_status'].get('latest_installable_revision', None)
        if it['status'] == 'Installed':
            installed_revisions_list.append({'name': it['name'],
                                             'owner': it['owner'],
                                             'tool_shed': it['tool_shed'],
                                             'revision': it.get('changeset_revision', None),
                                             'latest': latest})
    return installed_revisions_list


def update_tool_status(tool_shed_client, tool_id):
    """
    Given a `tool_shed_client` handle and and Tool Shed `tool_id`, return the
    installation status of the tool.
    """
    try:
        r = tool_shed_client.show_repository(tool_id)
        return r.get('status', 'NA')
    except Exception, e:
        log.warning('\tException checking tool {0} status: {1}'.format(tool_id, e))
        return 'NA'


def _tools_to_install(owners=['devteam', 'iuc'], return_formatted=False):
    """
    This is mostly a convenience method to jumpstart the tools list.

    Get a list of tools that should be installed. This list is composed by
    including all the non-package tools that are owned by `owners` from the Main
    Tool Shed.
    If `return_formatted` is set, return a list of dicts that have been formatted
    according to the required input file for installing tools (see other methods).

    *Note*: there is no way to programatically get a category a tool belongs in
    a Tool Shed so the returned list cannot simply be used as the input file but
    (manual!?!) adjustment is necessesary to provide tool category for each tool.
    """
    tsi = ToolShedInstance('https://toolshed.g2.bx.psu.edu')
    repos = tsi.repositories.get_repositories()
    tti = []  # tools to install
    for repo in repos:
        if repo['owner'] in owners and 'package' not in repo['name']:
            if return_formatted:
                repo = {'name': repo['name'], 'owner': repo['owner'],
                        'tool_shed_url': 'https://toolshed.g2.bx.psu.edu',
                        'tool_panel_section_id': ''}
            tti.append(repo)
    return tti


def parse_tool_list(tl):
    """
    A convenience method for parsing the output from an API call to a Galaxy
    instance listing all the tools installed on the given instance and
    formatting it for use by functions in this file.

    Sample GET call: `https://test.galaxyproject.org/api/tools?in_panel=true`.
    Via the API, call `gi.tools.get_tool_panel()` to get the list of tools on
    a given Galaxy instance `gi`.

    :type tl: list
    :param tl: A list of dicts with info about the tools

    :rtype: tuple of lists
    :return: The returned tuple contains two lists: the first one being a list
             of tools that were installed on the target Galaxy instance from
             the Tool Shed and the second one being a list of custom-installed
             tools. The ToolShed-list is YAML-formatted.

    Note that this method is rather coarse and likely to need some handholding.
    """
    ts_tools = []
    custom_tools = []

    for ts in tl:
        # print "%s (%s): %s" % (ts['name'], ts['id'], len(ts.get('elems', [])))
        for t in ts.get('elems', []):
            tid = t['id'].split('/')
            if len(tid) > 3:
                tool_already_added = False
                for added_tool in ts_tools:
                    if tid[3] in added_tool['name']:
                        tool_already_added = True
                if not tool_already_added:
                    ts_tools.append({'tool_shed_url': "https://{0}".format(tid[0]),
                                     'owner': tid[2],
                                     'name': tid[3],
                                     'tool_panel_section_id': ts['id']})
                # print "\t%s, %s, %s" % (tid[0], tid[2], tid[3])
            else:
                # print "\t%s" % t['id']
                custom_tools.append(t['id'])
    return ts_tools, custom_tools


def _list_tool_categories(tl):
    """
    Given a list of dicts `tl` as returned by the `parse_tool_list` method and
    where each list element holds a key `tool_panel_section_id`, return a list
    of unique section IDs.
    """
    category_list = []
    for t in tl:
        category_list.append(t.get('tool_panel_section_id'))
    return set(category_list)


def _parse_cli_options():
    """
    Parse command line options, returning `options` from `OptionParser`
    """
    parser = OptionParser(usage="usage: python %prog <options>")
    parser.add_option("-t", "--toolsfile",
                      dest="tool_list_file",
                      default=None,
                      help="Tools file to use (see tool_list.yaml.sample)",)
    parser.add_option("-d", "--dbkeysfile",
                      dest="dbkeys_list_file",
                      default=None,
                      help="Reference genome dbkeys to install (see "
                           "dbkeys_list.yaml.sample)",)
    parser.add_option("-a", "--apikey",
                      dest="api_key",
                      default=None,
                      help="Galaxy admin user API key",)
    parser.add_option("-g", "--galaxy",
                      dest="galaxy_url",
                      default=None,
                      help="URL for the Galaxy instance",)
    (options, args) = parser.parse_args()
    return options


def _flatten_tools_info(tools_info):
    """
    Flatten the dict containing info about what tools to install.

    The tool definition YAML file allows multiple revisions to be listed for
    the same tool. To enable simple, iterattive processing of the info in this
    script, flatten the `tools_info` list to include one entry per tool revision.

    :type tools_info: list of dicts
    :param tools_info: Each dict in this list should contain info about a tool.

    :rtype: list of dicts
    :return: Return a list of dicts that correspond to the input argument such
             that if an input element contained `revisions` key with multiple
             values, those will be returned as separate list items.
    """
    def _copy_dict(d):
        """
        Iterrate through the dictionary `d` and copy its keys and values
        excluding the key `revisions`.
        """
        new_d = {}
        for k, v in d.iteritems():
            if k != 'revisions':
                new_d[k] = v
        return new_d

    flattened_list = []
    for tool_info in tools_info:
        revisions = tool_info.get('revisions', [])
        if len(revisions) > 1:
            for revision in revisions:
                ti = _copy_dict(tool_info)
                ti['revision'] = revision
                flattened_list.append(ti)
        elif revisions:  # A single revisions was defined so keep it
            ti = _copy_dict(tool_info)
            ti['revision'] = revisions[0]
            flattened_list.append(ti)
        else:  # Revision was not defined at all
            flattened_list.append(tool_info)
    return flattened_list


def run_data_managers(options):
    """
    Run Galaxy Data Manager to download, index, and install reference genome
    data into Galaxy.

    :type options: OptionParser object
    :param options: command line arguments parsed by OptionParser
    """
    dbkeys_list_file = options.dbkeys_list_file
    kl = load_input_file(dbkeys_list_file)  # Input file contents
    dbkeys = kl['dbkeys']  # The list of dbkeys to install
    dms = kl['data_managers']  # The list of data managers to run
    galaxy_url = options.galaxy_url or kl['galaxy_instance']
    api_key = options.api_key or kl['api_key']
    gi = galaxy_instance(galaxy_url, api_key)

    istart = dt.datetime.now()
    errored_dms = []
    dbkey_counter = 0
    for dbkey in dbkeys:
        dbkey_counter += 1
        dbkey_name = dbkey.get('dbkey')
        dm_counter = 0
        for dm in dms:
            dm_counter += 1
            dm_tool = dm.get('id')
            # Initate tool installation
            start = dt.datetime.now()
            log.debug('[dbkey {0}/{1}; DM: {2}/{3}] Installing dbkey {4} with '
                      'DM {5}'.format(dbkey_counter, len(dbkeys), dm_counter,
                                      len(dms), dbkey_name, dm_tool))
            tool_input = dbkey
            try:
                response = gi.tools.run_tool('', dm_tool, tool_input)
                jobs = response.get('jobs', [])
                # Check if a job is actually running
                if len(jobs) == 0:
                    log.warning("\t(!) No '{0}' job found for '{1}'".format(dm_tool,
                                dbkey_name))
                    errored_dms.append({'dbkey': dbkey_name, 'DM': dm_tool})
                else:
                    # Monitor the job(s)
                    log.debug("\tJob running", extra={'same_line': True})
                    done_count = 0
                    while done_count < len(jobs):
                        done_count = 0
                        for job in jobs:
                            job_id = job.get('id')
                            job_state = gi.jobs.show_job(job_id).get('state', '')
                            if job_state == 'ok':
                                done_count += 1
                            elif job_state == 'error':
                                done_count += 1
                                errored_dms.append({'dbkey': dbkey_name, 'DM': dm_tool})
                        log.debug("", extra={'same_line': True})
                        time.sleep(10)
                    log.debug("\tDbkey '{0}' installed successfully in '{1}'".format(
                              dbkey.get('dbkey'), dt.datetime.now() - start))
            except ConnectionError, e:
                response = None
                end = dt.datetime.now()
                log.error("\t* Error installing dbkey {0} for DM {1} (after {2}): {3}"
                          .format(dbkey_name, dm_tool, end - start, e.body))
                errored_dms.append({'dbkey': dbkey_name, 'DM': dm_tool})
    log.info("All dbkeys & DMs listed in '{0}' have been processed.".format(dbkeys_list_file))
    log.info("Errored DMs: {0}".format(errored_dms))
    log.info("Total run time: {0}".format(dt.datetime.now() - istart))


def install_tools(options):
    """
    Parse the default input file and proceed to install listed tools.

    :type options: OptionParser object
    :param options: command line arguments parsed by OptionParser
    """
    istart = dt.datetime.now()
    tool_list_file = options.tool_list_file
    tl = load_input_file(tool_list_file)  # Input file contents
    tools_info = tl['tools']  # The list of tools to install
    galaxy_url = options.galaxy_url or tl['galaxy_instance']
    api_key = options.api_key or tl['api_key']
    gi = galaxy_instance(galaxy_url, api_key)
    tsc = tool_shed_client(gi)
    itl = installed_revisions(tsc)  # installed tools list

    responses = []
    errored_tools = []
    skipped_tools = []
    counter = 0
    tools_info = _flatten_tools_info(tools_info)
    total_num_tools = len(tools_info)
    default_err_msg = ('All repositories that you are attempting to install '
                       'have been previously installed.')

    # Process each tool/revision: check if it's already installed or install it
    for tool_info in tools_info:
        counter += 1
        already_installed = False  # Reset the flag
        tool = {}  # Payload for the tool we are installing
        # Copy required `tool_info` keys into the `tool` dict
        tool['name'] = tool_info.get('name', None)
        tool['owner'] = tool_info.get('owner', None)
        tool['tool_panel_section_id'] = tool_info.get('tool_panel_section_id', None)
        # Check if all required tool sections have been provided; if not, skip
        # the installation of this tool. Note that data managers are an exception
        # but they must contain string `data_manager` within the tool name.
        if not tool['name'] or not tool['owner'] or (not tool['tool_panel_section_id']
                                                     and 'data_manager' not in tool.get('name', '')):
            log.error("Missing required tool info field; skipping [name: '{0}'; "
                      "owner: '{1}'; tool_panel_section_id: '{2}']"
                      .format(tool['name'], tool['owner'], tool['tool_panel_section_id']))
            continue
        # Populate fields that can optionally be provided (if not provided, set
        # defaults).
        tool['install_tool_dependencies'] = \
            tool_info.get('install_tool_dependencies', True)
        tool['install_repository_dependencies'] = \
            tool_info.get('install_repository_dependencies', True)
        tool['tool_shed_url'] = \
            tool_info.get('tool_shed_url', 'https://toolshed.g2.bx.psu.edu/')
        ts = ToolShedInstance(url=tool['tool_shed_url'])
        # Get the set revision or set it to the latest installable revision
        tool['revision'] = tool_info.get('revision', ts.repositories.
                                         get_ordered_installable_revisions
                                         (tool['name'], tool['owner'])[-1])
        # Check if the tool@revision is already installed
        for installed in itl:
            if the_same_tool(installed, tool) and installed['revision'] == tool['revision']:
                log.debug("({0}/{1}) Tool {2} already installed at revision {3} "
                          "(Is latest? {4}). Skipping..."
                          .format(counter, total_num_tools, tool['name'],
                                  tool['revision'], installed['latest']))
                skipped_tools.append({'name': tool['name'], 'owner': tool['owner'],
                                      'revision': tool['revision']})
                already_installed = True
                break
        if not already_installed:
            # Initate tool installation
            start = dt.datetime.now()
            log.debug('(%s/%s) Installing tool %s from %s to section %s at '
                      'revision %s (TRT: %s)' %
                      (counter, total_num_tools, tool['name'], tool['owner'],
                       tool['tool_panel_section_id'], tool['revision'],
                       dt.datetime.now() - istart))
            try:
                response = tsc.install_repository_revision(
                    tool['tool_shed_url'], tool['name'], tool['owner'],
                    tool['revision'], tool['install_tool_dependencies'],
                    tool['install_repository_dependencies'],
                    tool['tool_panel_section_id'])
                tool_id = None
                tool_status = None
                if len(response) > 0:
                    tool_id = response[0].get('id', None)
                    tool_status = response[0].get('status', None)
                if tool_id and tool_status:
                    # Possibly an infinite loop here. Introduce a kick-out counter?
                    log.debug("\tTool installing", extra={'same_line': True})
                    while tool_status not in ['Installed', 'Error']:
                        log.debug("", extra={'same_line': True})
                        time.sleep(10)
                        tool_status = update_tool_status(tsc, tool_id)
                    end = dt.datetime.now()
                    log.debug("\tTool %s installed successfully (in %s) at revision %s"
                              % (tool['name'], str(end - start), tool['revision']))
                else:
                    end = dt.datetime.now()
                    log.error("\tCould not retrieve tool status for {0}".format(tool['name']))
            except ConnectionError, e:
                response = None
                end = dt.datetime.now()
                if default_err_msg in e.body:
                    log.debug("\tTool %s already installed (at revision %s)" %
                              (tool['name'], tool['revision']))
                else:
                    log.error("\t* Error installing a tool (after %s)! Name: %s,"
                              "owner: %s, revision: %s, error: %s" %
                              (tool['name'], str(end - start), tool['owner'],
                               tool['revision'], e.body))
                    errored_tools.append({'name': tool['name'], 'owner': tool['owner'],
                                          'revision': tool['revision'], 'error': e.body})
            outcome = {'tool': tool, 'response': response, 'duration': str(end - start)}
            responses.append(outcome)

    log.info("Skipped tools ({0}): {1}".format(
             len(skipped_tools), [(t['name'], t['revision']) for t in skipped_tools]))
    log.info("Errored tools ({0}): {1}".format(
             len(errored_tools), [(t['name'], t['revision']) for t in errored_tools]))
    log.info("All tools listed in '{0}' have been processed.".format(tool_list_file))
    log.info("Total run time: {0}".format(dt.datetime.now() - istart))

if __name__ == "__main__":
    global log
    log = _setup_global_logger()
    options = _parse_cli_options()
    if options.tool_list_file:
        install_tools(options)
    elif options.dbkeys_list_file:
        run_data_managers(options)
    else:
        log.error("Must provide tool list file or dbkeys list file. Look at usage.")
