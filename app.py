#%% Load Libraries
from action import Action
from pathlib import Path
from graphviz import Digraph,ENGINES
import requests
import yaml
import re

    


#%% Connect
act = Action()
act.login()

gh = act.ghConn


#%% Set variables
repos = act.get_repos().split(',')
print(repos)

#%% Generate
for repo_item in repos:
    output = []
    diagram = {"nodes": [],"edges": []}
    omit_diagram = {"nodes": [],"edges": []}

    print(f"Loading {repo_item}")
    repo = gh.get_repo(repo_item)
    files = repo.get_contents('.github/workflows')

    # Get file contents
    workflow_files = []
    for file in files:
        print(f"Loading {file}")
        content = requests.get(file.download_url)
        workflow_files.append({'name': file.name, 'content': content.text })

    # Print outline
    output.append(f"# Repository: {repo.name}")

    for file in workflow_files:
        if str(file['name']).endswith('.yml'):
            yfile = yaml.safe_load(file['content'])

            ### --> DIAGRAM NODE: WORKFLOW
            diagram['nodes'].append({
                "id": act.b64(file['name']), 
                "label": file['name'], 
                "type":"workflow", 
                "file_type":"yaml"
                })

    for file in workflow_files:
        if str(file['name']).endswith('.yml'):
            yfile = yaml.safe_load(file['content'])

            ## * WORKFLOW ################################
            current_workflow = act.b64(file['name'])
            output.append(f"\n### Workflow: {yfile['name']} ({file['name']})\n")
            previous_job = None
            for job in yfile['jobs']:

                ## * WORKFLOW > JOB ################################
                current_job = act.b64(current_workflow + job)
                output.append(f"- Job: {act.clean_title(job)}")

                if current_job not in diagram['nodes']:
                    ### --> DIAGRAM NODE: JOB IN WORKFLOW
                    diagram['nodes'].append({
                        "id": current_job, 
                        "label": act.clean_title(job), 
                        "belongs_to": current_workflow,
                        "type": "job", 
                        "file_type": "na"
                        })


                ### --> DIAGRAM EDGE: WORKFLOW CONTAINS JOB
                if previous_job:
                    diagram['edges'].append({
                        "source": previous_job,
                        "target": current_job,
                        "belongs_to": current_workflow,
                        "rel": "contains"
                        })
                else:
                    diagram['edges'].append({
                        "source": current_workflow,
                        "target": current_job,
                        "belongs_to": current_workflow,
                        "rel": "contains"
                        })

                if 'uses' in yfile['jobs'][job]:

                    ## * WORKFLOW > JOB > USES ################################
                    current_job_uses = act.b64(act.clean_uses(yfile['jobs'][job]['uses']))
                    node_item = yfile['jobs'][job]['uses']

                    output.append(f"\t- Uses: {act.clean_uses(yfile['jobs'][job]['uses'])}")

                    if str(yfile['jobs'][job]['uses']).endswith('.yml'):
                        if current_job_uses not in diagram['nodes']:
                            ### --> DIAGRAM NODE: WORKFLOW USING ANOTHER WORKFLOW
                            diagram['nodes'].append({
                                "id": current_job_uses, 
                                "label": act.clean_uses(node_item),
                                "type": "workflow", 
                                "file_type": "yaml"
                                })
                    else:
                        if act.b64(node_item) not in diagram['nodes']:
                            ### --> DIAGRAM NODE: JOB FROM GITHUB ACTION
                            diagram['nodes'].append({
                                "id": current_job_uses, 
                                "label": act.clean_uses(node_item), 
                                "type":"action", 
                                "file_type":"repository"
                                })
                    
                    ### --> DIAGRAM EDGE: WORKFLOW USES WORKFLOW
                    diagram['edges'].append({
                        "source": current_job,
                        "target": current_job_uses,
                        "rel": "uses"
                        })                

                if 'steps' in yfile['jobs'][job]:
                    step_cnt = 0
                    for step in yfile['jobs'][job]['steps']:
                        step_cnt = step_cnt + 1

                        node_item = f"{job}_step_{step_cnt}"

                        if step_cnt == 1:
                            previous_job_step = current_job
                        else:
                            previous_job_step = act.b64(current_workflow + f"{job}_step_{step_cnt-1}")

                        current_job_step = act.b64(current_workflow + node_item)

                        if 'name' in step:
                            ## * WORKFLOW > JOB > STEP (NAMED) ################################
                            output.append(f"\t- Step {step_cnt}: {act.clean_title(step['name'])}")

                            if current_job_step not in diagram['nodes']:
                                ### --> DIAGRAM NODE: STEP IN JOB
                                diagram['nodes'].append({
                                    "id": current_job_step, 
                                    "label": f"{act.clean_title(step['name'])}",
                                    "belongs_to": current_workflow,
                                    "type":"step", 
                                    "file_type":step_cnt
                                    })    
                        else:
                            ## * WORKFLOW > JOB > STEP (UNNAMED) ################################
                            output.append(f"\t- Step {step_cnt}:")

                            if current_job_step not in diagram['nodes']:
                                ### --> DIAGRAM NODE: STEP IN JOB
                                diagram['nodes'].append({
                                    "id": current_job_step, 
                                    "label": f"Step (Unnamed)", 
                                    "type":"step", 
                                    "file_type":step_cnt
                                    })

                        ### --> DIAGRAM EDGE: CONTAINS
                        diagram['edges'].append({
                            "source": previous_job_step,
                            "target": current_job_step,
                            "parent": current_job,
                            "belongs_to": current_workflow,
                            "rel": "contains"
                            }) 

                        if 'uses' in step:

                            ## * WORKFLOW > JOB > STEP > USES ################################
                            current_job_step_uses = act.b64(step['uses'])

                            output.append(f"\t\t- Uses: {act.clean_uses(step['uses'])}")

                            if current_job_step_uses not in diagram['nodes']:
                                ### --> DIAGRAM NODE: STEP FROM GITHUB ACTION
                                diagram['nodes'].append({
                                    "id": current_job_step_uses, 
                                    "label": act.clean_uses(step['uses']), 
                                    "type":"action", 
                                    "file_type":"repository"
                                    })

                            ### --> DIAGRAM EDGE: USES
                            diagram['edges'].append({
                                "source": current_job_step,
                                "target": current_job_step_uses,
                                "rel": "Uses"
                                }) 

                        if 'run' in step:
                            # output.append(f"\t- Run:\n\n")
                            # output.append(f"```\n{step['run']}```\n")
                            scripts = re.findall('/(.+?).sh', step['run'])
                            for script in scripts:

                                ## * WORKFLOW > JOB > STEP > RUN ################################
                                current_job_step_script = act.b64(f"{script}.sh")

                                output.append(f"\t\t- Script: `{script}.sh`")

                                node_item = f"{script}.sh"
                                if current_job_step_script not in diagram['nodes']:
                                    ### --> DIAGRAM NODE: STEP FROM SCRIPT
                                    diagram['nodes'].append({
                                        "id": act.b64(node_item), 
                                        "label": node_item, 
                                        "type":"script", 
                                        "file_type":"sh"
                                        })

                                ### --> DIAGRAM EDGE: USES
                                diagram['edges'].append({
                                    "source": current_job_step,
                                    "target": current_job_step_script,
                                    "rel": "Uses"
                                    }) 
                previous_job = current_job



    #%% Diagram
    graph_name = 'workflow_diagram'
    g = Digraph(graph_name, filename=graph_name, format='svg')
    g.attr(scale='2', label='Workflow Diagram', fontsize='12')



    colors = {
        "default":  '#cccccc',
        "action":   '#a6e6fc',
        "workflow": "#c3fca6",
        "job":      "#FFC355",
        "step":     "#FBE29d",
        "script":   "#eb6761"
    }

    g.attr('node', shape='box', style='filled')

    all_sub_ed = []
    for node in diagram['nodes']:
        fillcolor=colors['default']
        if node['type'] in colors:
            fillcolor = colors[node['type']]

        if 'belongs_to' in node:
            #** GROUP THE WORKFLOW ITEMS   
            with g.subgraph(name=f"cluster_{node['belongs_to']}") as job_group:

                sub_ed = []
                for edge in diagram['edges']:
                    if 'belongs_to' in edge and edge['belongs_to'] == node['belongs_to']:
                        entry = (edge['source'], edge['target'])
                        if entry not in all_sub_ed:
                            sub_ed.append(entry)
                            all_sub_ed.append(entry)
                job_group.attr(label="Workflow")
                
                job_group.node(node['id'], label=f"<{act.make_table(node)}>", fillcolor=fillcolor)
                job_group.edges(sub_ed)
            
        else:
            g.node(node['id'], label=f"<{act.make_table(node)}>", fillcolor=fillcolor)

    ed=[]
    for edge in diagram['edges']:
        if 'belongs_to' not in edge:
            entry = (edge['source'], edge['target'])
            if entry not in ed:
                ed.append((edge['source'], edge['target']))


    g.edges(ed)

    #
    # for engine in sorted(ENGINES):
    #     # if engine in ['fdp']:
    #     print(engine)
    #     g.engine = engine
    #     display.display(g)
    #     print()

    # dot or fdp
    # img = g._repr_mimebundle_(include=['image/png'])  
    g.render(filename=f"Workflows-{repo.name}", engine="dot")
    output.append(f"\n\n---\n\n![Graphical Representation of Workflow](Workflows-{repo.name}.svg)")
    # g.view()

    #
    g = None


    # Output
    # img = g._repr_mimebundle_(include=['image/png'])  
    # b64image = img['image/png']
    # output.append(f"![Graphical Representation of Workflow][1]")
    # output.append(f"[1]: data:image/png;base64,{b64image}")
    Path(f"Workflows-{repo.name}.md").write_text("\n".join(output))

# %%
