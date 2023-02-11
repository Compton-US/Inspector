from github import Github
from dotenv import load_dotenv
from graphviz import Digraph,ENGINES

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

    def make_diagram(self, nodes_and_edges, title='Workflow Diagram', colors={'default':'#cccccc'}, filename_prefix='Workflow'):
        g = Digraph(format='svg')
        g.attr(scale='2', label=title, fontsize='12')

        g.attr('node', shape='box', style='filled')

        all_sub_ed = []
        for node in nodes_and_edges['nodes']:
            fillcolor=colors['default']
            if node['type'] in colors:
                fillcolor = colors[node['type']]

            if 'belongs_to' in node:
                #** GROUP THE WORKFLOW ITEMS   
                with g.subgraph(name=f"cluster_{node['belongs_to']}") as job_group:

                    sub_ed = []
                    for edge in nodes_and_edges['edges']:
                        if 'belongs_to' in edge and edge['belongs_to'] == node['belongs_to']:
                            entry = (edge['source'], edge['target'])
                            if entry not in all_sub_ed:
                                sub_ed.append(entry)
                                all_sub_ed.append(entry)
                    job_group.attr(label="Workflow")
                    
                    job_group.node(node['id'], label=f"<{self.make_table(node)}>", fillcolor=fillcolor)
                    job_group.edges(sub_ed)
                
            else:
                g.node(node['id'], label=f"<{self.make_table(node)}>", fillcolor=fillcolor)

        ed=[]
        for edge in nodes_and_edges['edges']:
            if 'belongs_to' not in edge:
                entry = (edge['source'], edge['target'])
                if entry not in ed:
                    ed.append((edge['source'], edge['target']))


        g.edges(ed)

        # dot or fdp
        g.render(filename=filename_prefix, engine="dot")
        g = None

        return f"\n\n---\n\n![Graphical Representation of {title}]({filename_prefix}.svg)"