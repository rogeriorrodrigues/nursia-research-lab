"""Gera arquivos DICOM 100% sintéticos com identificadores brasileiros falsos.

CPF e CNS são válidos por algoritmo (o teste precisa achar o número inteiro),
mas gerados aleatoriamente e marcados como sintéticos. Nomes são fictícios óbvios.
"""
import random
from pydicom.dataset import Dataset, FileMetaDataset
from pydicom.sequence import Sequence
from pydicom.uid import ExplicitVRLittleEndian, generate_uid, CTImageStorage


def cpf_sintetico(rng):
    base = [rng.randint(0, 9) for _ in range(9)]
    for n in (10, 11):
        s = sum(d * p for d, p in zip(base, range(n, 1, -1)))
        r = (s * 10) % 11
        base.append(0 if r == 10 else r)
    d = "".join(map(str, base))
    return f"{d[:3]}.{d[3:6]}.{d[6:9]}-{d[9:]}"


def cns_sintetico(rng):
    # CNS definitivo começando com 7 (soma ponderada múltipla de 11)
    while True:
        d = [7] + [rng.randint(0, 9) for _ in range(14)]
        resto = sum(x * p for x, p in zip(d, range(15, 0, -1))) % 11
        if resto == 0:
            return "".join(map(str, d))
        # ajusta o último dígito quando possível
        for ult in range(10):
            d[-1] = ult
            if sum(x * p for x, p in zip(d, range(15, 0, -1))) % 11 == 0:
                return "".join(map(str, d))


def gera(n=60, seed=20261127):
    rng = random.Random(seed)
    arquivos = []
    for i in range(n):
        cpf, cns = cpf_sintetico(rng), cns_sintetico(rng)
        nome = f"FICTICIO^PACIENTE {i:02d}"
        nasc = f"19{rng.randint(40, 99)}{rng.randint(1, 12):02d}{rng.randint(1, 28):02d}"
        tel = f"(00) 9{rng.randint(1000, 9999)}-{rng.randint(1000, 9999)}"
        end = f"Rua Ficticia {rng.randint(1, 999)}, Bairro Exemplo"

        ds = Dataset()
        ds.file_meta = FileMetaDataset()
        ds.file_meta.MediaStorageSOPClassUID = CTImageStorage
        ds.file_meta.MediaStorageSOPInstanceUID = generate_uid()
        ds.file_meta.TransferSyntaxUID = ExplicitVRLittleEndian
        ds.SOPClassUID = CTImageStorage
        ds.SOPInstanceUID = ds.file_meta.MediaStorageSOPInstanceUID
        ds.StudyInstanceUID = generate_uid()
        ds.SeriesInstanceUID = generate_uid()
        ds.Modality = "CT"
        ds.StudyDate = "20261120"

        # Campos que o perfil de confidencialidade do DICOM manda tratar
        ds.PatientName = nome
        ds.PatientID = cpf.replace(".", "").replace("-", "")
        ds.OtherPatientIDs = cns
        ds.PatientBirthDate = nasc
        ds.PatientSex = rng.choice(["F", "M"])
        ds.PatientAddress = end
        ds.PatientTelephoneNumbers = tel
        ds.InstitutionName = "Hospital Ficticio de Exemplo"
        ds.InstitutionAddress = "Av. Inexistente 100"
        ds.ReferringPhysicianName = "DRA^FICTICIA"

        # Onde o identificador costuma escapar na prática: texto livre
        sorteio = rng.random()
        if sorteio < 0.4:
            ds.StudyDescription = f"TC TORAX - CPF {cpf}"
        else:
            ds.StudyDescription = "TC TORAX"
        if rng.random() < 0.5:
            ds.ImageComments = f"Paciente {nome.replace('^', ' ')}, CNS {cns}"
        if rng.random() < 0.3:
            ds.RequestedProcedureDescription = f"Retorno; contato {tel}"

        # Sequência aninhada com o nome de novo
        if rng.random() < 0.5:
            item = Dataset()
            item.RequestedProcedureID = "PROC01"
            item.ScheduledProcedureStepDescription = f"Agendado para {nome.replace('^', ' ')}"
            ds.RequestAttributesSequence = Sequence([item])

        # Bloco privado do "PACS" com o CPF
        if rng.random() < 0.5:
            bloco = ds.private_block(0x0009, "SINTETICO_PACS", create=True)
            bloco.add_new(0x01, "LO", cpf)

        ds.Rows = ds.Columns = 8
        ds.SamplesPerPixel = 1
        ds.PhotometricInterpretation = "MONOCHROME2"
        ds.BitsAllocated = ds.BitsStored = 16
        ds.HighBit = 15
        ds.PixelRepresentation = 0
        ds.PixelData = bytes(8 * 8 * 2)

        canarios = {"CPF": [cpf, ds.PatientID], "CNS": [cns], "nome": ["PACIENTE " + f"{i:02d}"],
                    "nascimento": [nasc], "telefone": [tel], "endereco": [end],
                    "instituicao": ["Hospital Ficticio"]}
        arquivos.append((ds, canarios))
    return arquivos
