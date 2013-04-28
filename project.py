'''
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
'''

# Include the python libraries
import cmd
import locale
import os
import pprint
import shlex

# Include the Dropbox SDK libraries
from dropbox import client, rest, session

# Tokens are cached here for the future access
TOKENS = 'dropbox_token.txt'

# You can find these values at http://www.dropbox.com/developers/apps
APP_KEY = 'gy60gre2uauivp2'
APP_SECRET = '3yvf1vsyj5y7pvo'
ACCESS_TYPE = 'dropbox' # should be 'dropbox' or 'app_folder' as configured for your app

# Checks if the token file exists or not
def check_for_file():
    return os.path.isfile(TOKENS)

# Prints the account information
def do_account_info(api_client):
    f = api_client.account_info()
    pprint.PrettyPrinter(indent=2).pprint(f)

def main():
    # If the TOKEN file exist
    if check_for_file():
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

    print "Successfully authenticated!"
    api_client = client.DropboxClient(sess)
    do_account_info(api_client)

if __name__ == '__main__':
    main()
