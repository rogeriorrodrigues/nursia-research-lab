"""Lê o specification.zip que o NuGet trouxe (Hl7.Fhir.Specification.Data.R4B 6.8.0)
e lista o que o perfil base R4B diz sobre os três casos que passaram:
o binding de Observation.code, o binding de Quantity.code e as invariantes do Bundle.

Uso (depois do dotnet run): python3 conferir_perfil.py > results/perfil-base.txt
"""
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

NS = {"f": "http://hl7.org/fhir"}
ZIP = Path(__file__).parent / "src" / "bin" / "Release" / "net8.0" / "specification.zip"


def sd(z, arquivo, url):
    with z.open(arquivo) as fh:
        for _, el in ET.iterparse(fh):
            if el.tag.endswith("StructureDefinition"):
                u = el.find("f:url", NS)
                if u is not None and u.get("value") == url:
                    return el


def elementos(defn):
    for e in defn.find("f:snapshot", NS).findall("f:element", NS):
        yield e.find("f:path", NS).get("value"), e


with zipfile.ZipFile(ZIP) as z:
    obs = sd(z, "profiles-resources.xml", "http://hl7.org/fhir/StructureDefinition/Observation")
    for p, e in elementos(obs):
        if p == "Observation.code":
            b = e.find("f:binding", NS)
            print(f"{p}: binding {b.find('f:strength', NS).get('value')} -> {b.find('f:valueSet', NS).get('value')}")
    qty = sd(z, "profiles-types.xml", "http://hl7.org/fhir/StructureDefinition/Quantity")
    for p, e in elementos(qty):
        if p in ("Quantity.code", "Quantity.system"):
            b = e.find("f:binding", NS)
            print(f"{p}: {'binding ' + b.find('f:strength', NS).get('value') if b is not None else 'sem binding'}")
        for c in e.findall("f:constraint", NS):
            if not c.find("f:key", NS).get("value").startswith(("ele-", "ext-")):
                print(f"{p}: {c.find('f:key', NS).get('value')} {c.find('f:human', NS).get('value')}")
    bun = sd(z, "profiles-resources.xml", "http://hl7.org/fhir/StructureDefinition/Bundle")
    print("Invariantes do Bundle (sem ele-/ext-):")
    for p, e in elementos(bun):
        for c in e.findall("f:constraint", NS):
            k = c.find("f:key", NS).get("value")
            if not k.startswith(("ele-", "ext-")):
                print(f"  {p}: {k} {c.find('f:human', NS).get('value')}")
