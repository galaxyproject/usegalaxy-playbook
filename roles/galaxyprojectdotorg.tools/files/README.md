Scripted tool installation
==========================

The Galaxy [Tool Shed][ts] provides a nice method for installing Galaxy
artifacts (e.g., tools, workflows) into a (remote) Galaxy instance. The task
of installing a significant number of artifacts can quickly become tedious if
using the GUI due to all the necessary clicking. For that reason, the Tool
Shed offers an [API][bb] that allows us to install any number of tools in an
automated way via a script.

`install_tool_shed_tools.py` is an example of such script. The script can be
used to install the tools and/or to run Galaxy [Data Managers][dm].

To install the tools, list the tools in a file that specify the tool name,
Tool Shed owner, and the Tool Shed url (see `tool_list.yaml.sample` for an
example of the exact format). Run the script as follows:

    python install_tool_shed_tools.py -t <tool list file>

File `tool_list.yaml` contains the list of tool that are installed
on [Galaxy Main][gm].

To run the Data Managers, create a file listing the genome dbkeys of interest
and a list of Data Managers that you'd like to run and invoke the script (see
`dbkeys_list.yaml.sample` for an example of the format). However, note this is
exoerimental implementation and you are likely to experience many issues.

    python install_tool_shed_tools.py -d <dbkey list file>

[ts]: http://genomebiology.com/2014/15/2/403
[bb]: http://bioblend.readthedocs.org/en/latest/api_docs/galaxy/all.html#module-bioblend.galaxy.toolshed
[dm]: https://wiki.galaxyproject.org/Admin/Tools/DataManagers
[gm]: https://usegalaxy.org/
