import re

def clean_company_name(name):
    name = name.lower().strip()
    name = re.sub(r"(pvt ltd|private limited|limited|ltd|corp|corporation|inc)", "", name)
    name = re.sub(r"[^a-z0-9 ]", "", name)
    return name.strip()
