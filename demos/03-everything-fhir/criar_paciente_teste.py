"""
Script auxiliar: cria o paciente JS no HAPI FHIR
=================================================
Caso você não tenha nenhum paciente pra testar o $everything,
esse script cria um paciente com histórico clínico compatível
com o caso JS do NursIA (ICC descompensada na UTI).

Cria: 1 Patient, 2 Conditions, 6 Observations, 2 MedicationRequests.
No final imprime o patient_id pra você usar no demo principal.

Uso:
  python criar_paciente_teste.py
"""

import requests
import json
from rich.console import Console

FHIR_URL = "http://localhost:8082/fhir"
console = Console()


def criar(recurso_tipo: str, payload: dict) -> dict:
    """POST genérico num endpoint FHIR."""
    url = f"{FHIR_URL}/{recurso_tipo}"
    resp = requests.post(
        url,
        json=payload,
        headers={"Content-Type": "application/fhir+json"},
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def main():
    console.print("\n[bold cyan]Criando paciente JS no HAPI FHIR...[/bold cyan]\n")

    # 1. Patient
    patient = criar("Patient", {
        "resourceType": "Patient",
        "name": [{"family": "Silva", "given": ["JS"]}],
        "gender": "male",
        "birthDate": "1957-03-15",
    })
    patient_id = patient["id"]
    console.print(f"[green]✓[/green] Patient criado: {patient_id}")

    ref = {"reference": f"Patient/{patient_id}"}

    # 2. Conditions (ICC + HAS)
    criar("Condition", {
        "resourceType": "Condition",
        "subject": ref,
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "code": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "42343007",
                "display": "Insuficiência cardíaca congestiva",
            }],
            "text": "ICC descompensada",
        },
    })
    console.print("[green]✓[/green] Condition: ICC descompensada")

    criar("Condition", {
        "resourceType": "Condition",
        "subject": ref,
        "clinicalStatus": {"coding": [{"code": "active"}]},
        "code": {
            "coding": [{
                "system": "http://snomed.info/sct",
                "code": "38341003",
                "display": "Hipertensão arterial sistêmica",
            }],
            "text": "HAS",
        },
    })
    console.print("[green]✓[/green] Condition: HAS")

    # 3. Observations (sinais vitais e labs)
    observacoes = [
        ("8480-6", "Pressão arterial sistólica", 84, "mmHg"),
        ("8462-4", "Pressão arterial diastólica", 52, "mmHg"),
        ("8867-4", "Frequência cardíaca", 118, "bpm"),
        ("2708-6", "Saturação de oxigênio", 94, "%"),
        ("2524-7", "Lactato", 3.6, "mmol/L"),
        ("33762-6", "BNP", 1860, "pg/mL"),
    ]

    for loinc, nome, valor, unidade in observacoes:
        criar("Observation", {
            "resourceType": "Observation",
            "subject": ref,
            "status": "final",
            "code": {
                "coding": [{
                    "system": "http://loinc.org",
                    "code": loinc,
                    "display": nome,
                }],
                "text": nome,
            },
            "valueQuantity": {
                "value": valor,
                "unit": unidade,
                "system": "http://unitsofmeasure.org",
            },
        })
        console.print(f"[green]✓[/green] Observation: {nome} = {valor} {unidade}")

    # 4. MedicationRequests
    medicacoes = [
        ("Noradrenalina 0.3 mcg/kg/min", "387480006"),
        ("Vasopressina 0.04 U/min", "387029005"),
    ]

    for nome, snomed in medicacoes:
        criar("MedicationRequest", {
            "resourceType": "MedicationRequest",
            "subject": ref,
            "status": "active",
            "intent": "order",
            "medicationCodeableConcept": {
                "coding": [{
                    "system": "http://snomed.info/sct",
                    "code": snomed,
                }],
                "text": nome,
            },
        })
        console.print(f"[green]✓[/green] MedicationRequest: {nome}")

    # Final
    console.print(f"\n[bold green]Pronto![/bold green]")
    console.print(f"[bold]Patient ID:[/bold] {patient_id}")
    console.print(f"\n[dim]Testa o $everything com:[/dim]")
    console.print(f"[cyan]python demo_everything_fhir.py {patient_id}[/cyan]")
    console.print(f"\n[dim]Ou via curl:[/dim]")
    console.print(f"[cyan]curl {FHIR_URL}/Patient/{patient_id}/$everything[/cyan]\n")


if __name__ == "__main__":
    main()
