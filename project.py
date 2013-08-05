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
import locale, cmd
import os, random, struct
import pprint, shlex, sys, re
from Crypto.Cipher import AES
from re import sub

# Include the Dropbox SDK libraries
from dropbox import client, rest, session

# Tokens are cached here for the future access
TOKENS = 'dropbox_token.txt'

# Man page 
HELP = 'help'

# You can find these values at http://www.dropbox.com/developers/apps
APP_KEY = 'gy60gre2uauivp2'
APP_SECRET = '3yvf1vsyj5y7pvo'

# This key is used to encrypt and decrypt the data
KEY = "rU4Debxe2zKqSxNrUSUUk9AS"

ACCESS_TYPE = 'dropbox' # should be 'dropbox' or 'app_folder' as configured for your app


class Dropbox(cmd.Cmd):
    def __init__ (self):
        cmd.Cmd.__init__(self)

        # If number of arguments is less than 4
        if len(sys.argv) < 4:
            self.do_help()
            sys.exit(0)

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

        print "Successfully authenticated!\n"
        self.api_client = client.DropboxClient(sess)
        #self.do_account_info(api_client)
        
        if (sys.argv[1] == 'put'):
            self.do_put(sys.argv[2], sys.argv[3])
        elif (sys.argv[1] == 'get'):
            self.do_get(sys.argv[2], sys.argv[3])
        else:
            print "Invalid argument[1]"

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
        to_file = open(os.path.expanduser(from_path), "wb")
        f, metadata = self.api_client.get_file_and_metadata(from_path)

        print 'Metadata:', metadata
        to_file.write(f.read())
        print "Successfully downloaded the encrypted file"

        self.do_decrypt_file(KEY, from_path, to_path) 
        print "Successfully decrypted the downloaded file"
    
    # A function to upload files into dropbox account
    def do_put(self, from_path, to_path=None):
        """
        Copy local file to Dropbox

        Example:
        $ python project.py put /home/$USER/file.txt dropbox-file.txt
        """
        # Sanitization checking
        if os.path.isfile(from_path):
            self.do_encrypt_file(KEY, from_path)
            print "Local file encryption was successfull"
            out_filename = from_path + '.enc'

            if not to_path:
                to_path = '~/' + out_filename

            from_file = open(os.path.expanduser(out_filename), "rb")
            self.api_client.put_file(to_path, from_file)
                       
            # Cleans up the .enc files
            os.remove(out_filename)
            
            print "Encrypted File Successfully Uploaded!"

        else:
            print "Give a valid input file"
            sys.exit(0)
    
    # Function prints the help text from the 'help' file
    def do_help(self):
        f = open (HELP, 'r')
        for line in f:
            sys.stdout.write(line)

    def do_encrypt_file(self, key, in_filename, out_filename, chunksize=64*1024):
        """ Encrypts a file using AES (CBC mode) with the
            given key.

            key:
                The encryption key - a string that must be
                either 16, 24 or 32 bytes long. Longer keys
                are more secure.

            in_filename:
                Name of the input file

            out_filename:
                If None, '<in_filename>.enc' will be used.

            chunksize:
                Sets the size of the chunk which the function
                uses to read and encrypt the file. Larger chunk
                sizes can be faster for some files and machines.
                chunksize must be divisible by 16.
        """
        iv = ''.join(chr(random.randint(0, 0xFF)) for i in range(16))
        encryptor = AES.new(key, AES.MODE_CBC, iv)
        filesize = os.path.getsize(in_filename)

        with open(in_filename, 'rb') as infile:
            with open(out_filename, 'wb') as outfile:
                outfile.write(struct.pack('<Q', filesize))
                outfile.write(iv)

                while True:
                    chunk = infile.read(chunksize)
                    if len(chunk) == 0:
                        break
                    elif len(chunk) % 16 != 0:
                        chunk += ' ' * (16 - len(chunk) % 16)

                    outfile.write(encryptor.encrypt(chunk))
              

    def do_decrypt_file(self, key, in_filename, out_filename, chunksize=24*1024):
        """ Decrypts a file using AES (CBC mode) with the
            given key. Parameters are similar to encrypt_file,
            with one difference: out_filename, if not supplied
            will be in_filename without its last extension
            (i.e. if in_filename is 'aaa.zip.enc' then
            out_filename will be 'aaa.zip')
        """
        with open(in_filename, 'rb') as infile:
            origsize = struct.unpack('<Q', infile.read(struct.calcsize('Q')))[0]
            iv = infile.read(16)
            decryptor = AES.new(key, AES.MODE_CBC, iv)

            with open(out_filename, 'wb') as outfile:
                while True:
                    chunk = infile.read(chunksize)
                    if len(chunk) == 0:
                        break
                    outfile.write(decryptor.decrypt(chunk))
                outfile.truncate(origsize)

def main():
    drop = Dropbox()


if __name__ == '__main__':
    main()
