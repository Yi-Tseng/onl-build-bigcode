#!/usr/bin/env python3
################################################################
#
#        Copyright 2013, Big Switch Networks, Inc.
#
# Licensed under the Eclipse Public License, Version 1.0 (the
# "License") you may not use this file except in compliance
# with the License. You may obtain a copy of the License at
#
#        http://www.eclipse.org/legal/epl-v10.html
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific
# language governing permissions and limitations under the
# License.
#
################################################################
#
#
# Build the ucli_module_t structure based on functions
# define in the given source files.
#
################################################################
import sys
import re
import os

# import from wod
def write_on_diff(fname, new, msg=True):
    if type(new) == bytes:
        new = new.decode("utf8")
    existing = None
    if os.path.exists(fname):
        with open(fname, "r") as f:
            existing=f.read()

    if new == existing:
        if msg:
            print("%s: no changes." % fname)
    else:
        if msg:
            print("%s: updated." % fname)
        with open(fname, "w") as f:
            f.write(new)


#
# Find all ucli command handlers in the given source file.
#
# They all have the format ucli_status_t (name)(ucli_context_t* [var])
#
source = None
with open(sys.argv[1], "r") as f:
    source = f.read()

matches = re.findall("(?P<condition>#if.*?\n)?(?:\s*static\s*)?ucli_status_t\s+(?P<function>[_a-zA-Z]\w*)\(\s*ucli_context_t\s*\*\s*[_a-zA-Z]\w*\s*\)", source)

modules = {}
for m in matches:
    # Handler naming format is:
    #
    # [prefix]_ucli_[moduleName]_[command]
    fields = m[1].split("_")
    prefix = fields[0]
    if fields[1] != "ucli":
        raise Exception("Bad format for handler name: %s" % (m))
    module = fields[2]

    if not (prefix, module) in modules:
        modules[(prefix, module)] = []

    d = {}
    d['name'] = m[1]
    d['condition'] = None
    if m[0]:
        d['condition'] = m[0].replace("/*","").replace("*/","").replace("condition:","").strip()

    modules[(prefix,module)].append(d)



# Regenerate the handler tables
start = "/* <auto.ucli.handlers.start> */"
end   = "/* <auto.ucli.handlers.end> */"

s = start
s += """
/******************************************************************************
 *
 * These handler table(s) were autogenerated from the symbols in this
 * source file.
 *
 *****************************************************************************/
"""


for ((p,m), lst) in modules.items():
    s += "static ucli_command_handler_f %s_ucli_%s_handlers__[] = \n" % (p,m)
    s += "{\n"
    for h in lst:
        if h['condition']:
            s += "%s\n" % h['condition']
        s+= "    %s,\n" % (h['name'])
        if h['condition']:
            s += "#endif\n"

    s += "    NULL\n"
    s += "}\n"
s += "/******************************************************************************/\n"
s += end

# Replace old handler tables
rstart = re.sub("\*", "\\\*", start)
rend = re.sub("\*", "\\\*", end)
expr = rstart + ".*" + rend
source = re.sub(expr, s, source, flags=re.DOTALL)
write_on_diff(sys.argv[1], source)






