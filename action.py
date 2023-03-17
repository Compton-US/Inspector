from github import Github
from dotenv import load_dotenv
from graphviz import Digraph,ENGINES
from nested_lookup import nested_lookup

import matplotlib.colors as mc
import colorsys
import numpy as np

import os, sys, pypandoc
import base64


class Action(object):
    ghConn = None

    def get_prefix(self):
        load_dotenv()
        prefix = "Project"

        if 'file_prefix' in os.environ:
            prefix = os.environ.get('file_prefix')

        return f"{prefix}"       


    def get_path_and_prefix(self):
        load_dotenv()
        prefix = "Project"
        path = "output"

        if 'file_prefix' in os.environ:
            prefix = os.environ.get('file_prefix')

        if 'output_path' in os.environ:
            path = os.environ.get('output_path')

        return f"{path}/{prefix}"       

    def generate(self,org,repo,project,toc=False,pdf=False,output='.'):
        self.login()
        self.builder(org,repo,project,toc,pdf,output)

    def login(self):
        load_dotenv()
        if 'WORKFLOW_GITHUB_TOKEN' in token:
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

    def make_table(self, node, width=300):
        return f"""
        <TABLE width='{width}'>
            <TR><td width='{width}'><b>{node['type'].upper()}</b> <i>{node['file_type']}</i></td></TR>
            <TR><td width='{width}'>{node['label']}</td></TR>
        </TABLE>
        """

    def make_width(self,input,factor=5,min=50):
        width = len(input) * factor

        if width < min:
            return min
            
        return width


    def b64(self, string):
        return str(base64.b64encode(string.encode('ascii')))

    def make_color(self, color, amount=.30):
        # Based on : https://gist.github.com/technic/8bf3932ad7539b762a05da11c0093ed5
        try:
            c = mc.cnames[color]
        except:
            c = color
        c = np.array(colorsys.rgb_to_hls(*mc.to_rgb(c)))
        (r, g, b) = colorsys.hls_to_rgb(c[0],amount,c[2])

        return mc.to_hex([r, g, b])

    def make_diagram(self, nodes_and_edges, title='Workflow Diagram', colors={'default':'#cccccc'}, filename='Overview', box_width=50):
        g = Digraph(format='svg')
        g.attr(scale='2', label=title, fontsize='16')

        g.attr('node', shape='box', style='filled', fontsize='16')

        all_sub_ed = []

        workflow_nodes_width = box_width
        other_nodes_width = box_width
        for node in nodes_and_edges['nodes']:
            current_width = self.make_width(node['label'])
            if ('belongs_to' in node or node['type'] == 'workflow') and current_width > workflow_nodes_width:
                workflow_nodes_width = current_width
            elif 'belongs_to' not in node and current_width > other_nodes_width:
                other_nodes_width = current_width


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
                    job_group.attr(
                        label="Workflow", 
                        penwidth="4", 
                        color=self.make_color(colors['workflow'],.4),
                        margin="50.0,50.0"
                        )

                    custom_color = self.make_color(colors[node['type']])
                    job_group.node(node['id'], 
                        label=f"<{self.make_table(node, workflow_nodes_width)}>",
                        fillcolor=fillcolor, 
                        penwidth="4",
                        color=self.make_color(fillcolor,.4))
                    job_group.attr('edge',arrowsize="1",weight="2",color=custom_color, penwidth="4")
                    job_group.edges(sub_ed)
                
            else:
                node_width = other_nodes_width
                if node['type'] == 'workflow':
                    node_width = workflow_nodes_width

                g.node(node['id'], label=f"<{self.make_table(node, node_width)}>", fillcolor=fillcolor, penwidth="4",color=self.make_color(fillcolor,.4))

        ed=[]
        for edge in nodes_and_edges['edges']:
            if 'belongs_to' not in edge:
                entry = (edge['source'], edge['target'])
                if entry not in ed:
                    ed.append((edge['source'], edge['target']))

        g.attr('edge',arrowsize="2",weight="4",color=colors['line'], penwidth="3")
        g.edges(ed)

        # dot or fdp
        g.render(filename=f"{self.get_path_and_prefix()}{filename}", engine="dot")
        g = None

        return self.diagram_markdown(title, filename)
    
    def make_workflow_diagram(self, workflow, diagram, colors={'default':'#cccccc'}, filename='Workflow'):
        workflow_diagram = {"nodes": [],"edges": []}
        workflow_diagram['nodes'].append(workflow)

        for edge in diagram['edges']:
            if 'belongs_to' in edge and edge['belongs_to'] == workflow['id']:
                workflow_diagram['edges'].append(edge)
            elif 'used_by' in edge and edge['used_by'] == workflow['id']:
                workflow_diagram['edges'].append(edge)

        identifiers = nested_lookup('source',workflow_diagram['edges']) + nested_lookup('target',workflow_diagram['edges'])

        for node in diagram['nodes']:
            if node['id'] in identifiers:
                workflow_diagram['nodes'].append(node)

        result = self.make_diagram(workflow_diagram, colors=colors, filename=filename)
        return result
    

    def diagram_markdown(self, title, filename):
        filename = f"{self.get_prefix()}{filename}"
        return f"\n\n---\n\n![Graphical Representation of {title}]({filename}.svg)"