"""
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

# Include the python libraries
import cmd
import locale
import os
import pprint
import shlex
import sys
import re

# Include the Dropbox SDK libraries
from dropbox import client, rest, session

# Tokens are cached here for the future access
TOKENS = 'dropbox_token.txt'

# Man page 
HELP = 'help'

# You can find these values at http://www.dropbox.com/developers/apps
APP_KEY = 'gy60gre2uauivp2'
APP_SECRET = '3yvf1vsyj5y7pvo'
ACCESS_TYPE = 'dropbox' # should be 'dropbox' or 'app_folder' as configured for your app


class Dropbox(cmd.Cmd):
    def __init__ (self):
        cmd.Cmd.__init__(self)

        # If number of arguments is less than 4
        if len(sys.argv) < 4:
            self.do_help()
        #    sys.exit(0)

        # If the TOKEN file exist
        if os.path.isfile(TOKENS):
            token_file = open(TOKENS)
            token_key,token_secret = token_file.read().split('|')
            token_file.close()

            sess = session.DropboxSession(APP_KEY,APP_SECRET, ACCESS_TYPE )
            sess.set_token(token_key,token_secret)

        # If the TOKEN file doesn't exist
        else:
            sess = session.DropboxSession(APP_KEY, APP_SECRET, ACCESS_TYPE)
            request_token = sess.obtain_request_token()
            url = sess.build_authorize_url(request_token)

            # Make the user sign in and authorize this token
            print "url:", url
            print "Please copy paste this url into your web browser and press the 'Allow' button, then hit 'Enter' here."
            raw_input()

            # This will fail if the user didn't visit the above URL and hit 'Allow'
            access_token = sess.obtain_access_token(request_token)

            token_file = open(TOKENS,'w')
            token_file.write("%s|%s" % (access_token.key,access_token.secret) )
            token_file.close()

        print "Successfully authenticated!\nRetrieving user information from server\n"
        api_client = client.DropboxClient(sess)
        self.do_account_info(api_client)
        
        if (sys.argv[1] == 'put'):
            self.do_put(sys.argv[2], sys.argv[3])
        elif (sys.argv[1] == 'get'):
            self.do_get(sys.argv[2], sys.argv[3])
        else:
            print "Invalid input" + sys.argv[1]

    # Function prints the account information
    def do_account_info(self, api_client):
        f = api_client.account_info()
        pprint.PrettyPrinter(indent=2).pprint(f)

    # A function to download files from dropbox account
    def do_get(self, from_path, to_path):
        """
        Copy file from Dropbox to local file and print out out the metadata.

        Example:
        $ python project.py get dropbox-file.txt.enc /home/$USER/file.txt
        """
        # Sanitization checking
        if os.path.isfile(from_path):
            print "File exist"

        else:
            print "Give a valid input file"
            sys.exit(0)

    # A function to upload files into dropbox account
    def do_put(self, from_path, to_path):
        """
        Copy local file to Dropbox

        Example:
        $ python project.py put /home/$USER/file.txt dropbox-file.txt
        """
        # Sanitization checking
        if os.path.isfile(from_path):
            print "File exist"

        else:
            print "Give a valid input file"
            sys.exit(0)
    
    # Function prints the help text from the 'help' file
    def do_help(self):
        f = open (HELP, 'r')
        for line in f:
            sys.stdout.write(line)

def main():
    drop = Dropbox()


if __name__ == '__main__':
    main()
