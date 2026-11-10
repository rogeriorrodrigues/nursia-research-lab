---
name: mascarar-identificadores
description: Valida, conta e mascara CPF e CNS (Cartão Nacional de Saúde) em texto livre. Use quando o usuário pedir pra checar um CPF ou CNS, contar identificadores numa nota ou tirar CPF e CNS de um texto antes de mandar pra outro sistema.
---

# Mascarar identificadores brasileiros

Todas as ações leem o texto pelo stdin e devolvem JSON numa linha.

## Ações

| ação | o que faz | devolve |
|---|---|---|
| `validar_cpf` | confere os dois dígitos verificadores de um CPF, com ou sem pontuação | `true` ou `false` |
| `validar_cns` | confere o CNS (15 dígitos) pela soma ponderada módulo 11 | `true` ou `false` |
| `mascarar_identificadores` | troca CPF e CNS válidos por `[CPF]` e `[CNS]`; número inválido fica como está | o texto mascarado |
| `contar_identificadores` | conta CPF e CNS válidos e inválidos, sem devolver os números | `{"cpf_validos": n, ...}` |

## Como chamar

```bash
echo "texto" | python scripts/identificadores.py mascarar_identificadores
```

## Regras

- Nunca repita na resposta o CPF ou o CNS original. Use a saída do script.
- Se o texto tiver mais de um identificador, prefira `contar_identificadores` antes de mascarar, pra dizer ao usuário quantos foram trocados.
- Número que falha no dígito verificador não é mascarado. Avise o usuário quando `cpf_invalidos` ou `cns_invalidos` for maior que zero.
