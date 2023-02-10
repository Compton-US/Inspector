from github import Github
from dotenv import load_dotenv
import os, sys, pypandoc
import base64

class Action(object):
    ghConn = None

    def generate(self,org,repo,project,toc=False,pdf=False,output='.'):
        self.login()
        self.builder(org,repo,project,toc,pdf,output)

    def login(self):
        load_dotenv()
        token = os.environ.get('WORKFLOW_GITHUB_TOKEN')
        if token == None:
            print("Error: Check that you have the WORKFLOW_GITHUB_TOKEN variable set.\n")
            sys.exit(1)
        self.ghConn = Github(token)

    def get_repos(self):
        load_dotenv()
        repos = os.environ.get('REPOS')

        if repos == None:
            print("Error: Check that you have the REPOS variable set.\n")
            sys.exit(1)

        return repos
    
    def clean_uses(self, input):
        if str(input).rfind('@') > 0:
            (name,hash) = input.split('@')
            return name
        
        return str(input).replace('./.github/workflows/','')
    
    def clean_title(self, input):
        if str(input).rfind('-') > 0:
            result = f"{str(input).replace('-',' ').title()} ({input})"
            return result
        
        result = str(input).title()    
        result = result.replace('Oscal','OSCAL')
        result = result.replace('Jdk','JDK')
        result = result.replace('Xml','XML')

        return result   

    def make_table(self, node):
        return f"""
        <TABLE>
            <TR><td><b>{node['type'].upper()}</b> <i>{node['file_type']}</i></td></TR>
            <TR><td>{node['label']}</td></TR>
        </TABLE>
        """

    def b64(self, string):
        return str(base64.b64encode(string.encode('ascii')))