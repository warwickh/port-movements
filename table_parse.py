import pandas as pd
from bs4 import BeautifulSoup 

containers = ["FCIU7037660","TCLU8072263"]
for container in containers:

    with open('%s_status.txt'%container, 'r', encoding="utf-8") as f:
        content = f.read()
        cont_soup = BeautifulSoup(content, "html.parser")
        #updates = cont_soup.find_all("form", {"name": "tracing_by_container_f"})
        #print(updates)
        #for update in updates:
        table = pd.read_html(content, attrs={"id": "tracing_by_container_f:hl66"})[0]
        print(table)
        print(table.to_dict('records'))