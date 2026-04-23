#!/bin/bash
# demo-everything.sh
# Screen record: $everything FHIR — cru vs filtrado
# Uso: ./demo-everything.sh

set -e

# ============ CONFIGURAÇÃO ============
FHIR_URL="${FHIR_URL:-http://localhost:8082/fhir}"
PATIENT_ID="${PATIENT_ID:?Defina export PATIENT_ID=xxx antes de rodar}"

# Cores ANSI para destaque visual
BOLD='\033[1m'
RED='\033[91m'
GREEN='\033[92m'
YELLOW='\033[93m'
CYAN='\033[96m'
DIM='\033[2m'
RESET='\033[0m'

# ============ FUNÇÕES ============

pausa() {
  sleep "${1:-2}"
}

separador() {
  echo ""
  echo -e "${DIM}────────────────────────────────────────────────${RESET}"
  echo ""
}

# ============ EXECUÇÃO ============

clear

# CENA 1 — TÍTULO (aparece de uma vez)
cat <<EOF

  ${BOLD}\$everything FHIR${RESET} — cru vs filtrado

  ${DIM}um endpoint, dois comportamentos${RESET}

EOF
pausa 3

# CENA 2 — BUNDLE CRU
echo -e "${BOLD}${YELLOW}▶ 1/2  Chamada SEM parâmetros${RESET}"
echo ""
echo -e "${DIM}GET ${FHIR_URL}/Patient/${PATIENT_ID}/\$everything${RESET}"
pausa 2
echo -e "${DIM}  baixando bundle...${RESET}"

curl -s "${FHIR_URL}/Patient/${PATIENT_ID}/\$everything?_count=10000" > /tmp/bundle_cru.json

CRU_BYTES=$(wc -c < /tmp/bundle_cru.json)
CRU_KB=$(awk "BEGIN {printf \"%.1f\", $CRU_BYTES/1024}")
CRU_ENTRIES=$(jq '.entry | length' /tmp/bundle_cru.json)
CRU_TOKENS=$((CRU_BYTES / 4))

echo ""
echo -e "${RED}┌─────────────────────────────────────────────┐${RESET}"
echo -e "${RED}│${RESET}  Tamanho:  ${BOLD}${CRU_KB} KB${RESET}"
echo -e "${RED}│${RESET}  Entries:  ${BOLD}${CRU_ENTRIES}${RESET}"
echo -e "${RED}│${RESET}  Tokens:   ${BOLD}~${CRU_TOKENS}${RESET}  ${DIM}(estimado)${RESET}"
echo -e "${RED}└─────────────────────────────────────────────┘${RESET}"
echo ""
pausa 3

echo -e "${BOLD}Recursos no Bundle:${RESET}"
jq -r '
  [.entry[].resource.resourceType]
  | group_by(.)
  | map({tipo: .[0], qtd: length})
  | sort_by(-.qtd)
  | .[]
  | "  \(.tipo | . + (" " * (25 - length))) \(.qtd)"
' /tmp/bundle_cru.json

pausa 4

separador

# CENA 3 — BUNDLE FILTRADO
echo -e "${BOLD}${GREEN}▶ 2/2  Chamada COM _type restritivo${RESET}"
echo ""
echo -e "${DIM}GET ${FHIR_URL}/Patient/${PATIENT_ID}/\$everything${RESET}"
echo -e "${DIM}    ?_type=Condition,MedicationRequest${RESET}"
echo -e "${DIM}    &_count=10000${RESET}"
pausa 2
echo -e "${DIM}  baixando bundle...${RESET}"

curl -s "${FHIR_URL}/Patient/${PATIENT_ID}/\$everything?_type=Condition,MedicationRequest&_count=10000" > /tmp/bundle_filtrado.json

FIL_BYTES=$(wc -c < /tmp/bundle_filtrado.json)
FIL_KB=$(awk "BEGIN {printf \"%.1f\", $FIL_BYTES/1024}")
FIL_ENTRIES=$(jq '.entry | length' /tmp/bundle_filtrado.json)
FIL_TOKENS=$((FIL_BYTES / 4))

REDUCAO=$(awk "BEGIN {printf \"%.0f\", (1 - $FIL_BYTES / $CRU_BYTES) * 100}")

echo ""
echo -e "${GREEN}┌─────────────────────────────────────────────┐${RESET}"
echo -e "${GREEN}│${RESET}  Tamanho:  ${BOLD}${FIL_KB} KB${RESET}"
echo -e "${GREEN}│${RESET}  Entries:  ${BOLD}${FIL_ENTRIES}${RESET}"
echo -e "${GREEN}│${RESET}  Tokens:   ${BOLD}~${FIL_TOKENS}${RESET}  ${DIM}(estimado)${RESET}"
echo -e "${GREEN}│${RESET}  ${BOLD}${CYAN}Redução:  ${REDUCAO}%${RESET}"
echo -e "${GREEN}└─────────────────────────────────────────────┘${RESET}"
echo ""
pausa 3

echo -e "${BOLD}Recursos no Bundle:${RESET}"
jq -r '
  [.entry[].resource.resourceType]
  | group_by(.)
  | map({tipo: .[0], qtd: length})
  | sort_by(-.qtd)
  | .[]
  | "  \(.tipo | . + (" " * (25 - length))) \(.qtd)"
' /tmp/bundle_filtrado.json

pausa 4

separador

# CENA 4 — RESUMO DO PRONTUÁRIO
echo -e "${BOLD}${CYAN}╭──────────────────────────────────────────────────────╮${RESET}"
echo -e "${BOLD}${CYAN}│${RESET}  ${BOLD}PRONTUÁRIO DO PACIENTE${RESET}                              ${BOLD}${CYAN}│${RESET}"
echo -e "${BOLD}${CYAN}│${RESET}  ${DIM}extraído do bundle filtrado${RESET}                         ${BOLD}${CYAN}│${RESET}"
echo -e "${BOLD}${CYAN}╰──────────────────────────────────────────────────────╯${RESET}"
echo ""

# Contagens (do bundle filtrado)
COND_TOTAL=$(jq '[.entry[].resource | select(.resourceType == "Condition")] | length' /tmp/bundle_filtrado.json)
MED_TOTAL=$(jq '[.entry[].resource | select(.resourceType == "MedicationRequest")] | length' /tmp/bundle_filtrado.json)

# ▪ Identificação
echo -e "${BOLD}${YELLOW}▪ IDENTIFICAÇÃO${RESET}"
echo -e "${DIM}  ────────────────${RESET}"
jq -r '
  .entry[].resource | select(.resourceType == "Patient")
  | "  [1m\((.name[0].prefix[0] // "") + " " + (.name[0].given | join(" ")) + " " + .name[0].family | sub("^ +"; ""))[0m",
    "  [2mPatient/[0m\(.id)  ·  \(.gender)  ·  nasc. [96m\(.birthDate)[0m\(if .deceasedDateTime then "  ·  [91m⚠ óbito \(.deceasedDateTime[0:10])[0m" else "" end)"
' /tmp/bundle_filtrado.json

pausa 2
echo ""

# ▪ Condições
echo -e "${BOLD}${YELLOW}▪ CONDIÇÕES${RESET}  ${DIM}──────────── últimas 5 de ${COND_TOTAL}${RESET}"
jq -r --arg width 55 '
  [.entry[].resource | select(.resourceType == "Condition")]
  | sort_by(.onsetDateTime // "") | reverse | .[0:5] | .[]
  | (.code.text // .code.coding[0].display // "?") as $desc
  | "  [96m\(.onsetDateTime[0:10])[0m  •  " + (if ($desc | length) > ($width | tonumber) then ($desc[0:($width | tonumber)-1]) + "…" else $desc end)
' /tmp/bundle_filtrado.json

pausa 2
echo ""

# ▪ Medicações
echo -e "${BOLD}${YELLOW}▪ MEDICAÇÕES${RESET}  ${DIM}──────────── últimas 5 de ${MED_TOTAL}${RESET}"
jq -r --arg width 45 '
  (reduce (.entry[].resource | select(.resourceType == "Medication")) as $m ({}; .[$m.id] = ($m.code.text // $m.code.coding[0].display // "?"))) as $meds
  | [.entry[].resource | select(.resourceType == "MedicationRequest")]
  | sort_by(.authoredOn // "") | reverse | .[0:5] | .[]
  | (.medicationCodeableConcept.text // $meds[(.medicationReference.reference | split("/")[-1])] // "?") as $name
  | ($width | tonumber) as $w
  | (if ($name | length) > $w then ($name[0:$w-1]) + "…" else $name + (" " * ($w - ($name | length))) end) as $padded
  | "  [96m\(.authoredOn[0:10])[0m  •  " + $padded + "  [2m[\(.status)][0m"
' /tmp/bundle_filtrado.json

pausa 3
echo ""

# ▪ Evoluções clínicas
echo -e "${DIM}  baixando evoluções...${RESET}"
curl -s "${FHIR_URL}/DocumentReference?patient=${PATIENT_ID}&_count=100&_sort=-date" > /tmp/bundle_notas.json
NOTES_FETCHED=$(jq '.entry | length' /tmp/bundle_notas.json)
echo -e "${BOLD}${YELLOW}▪ EVOLUÇÕES CLÍNICAS${RESET}  ${DIM}──────────── 3 amostras de ${NOTES_FETCHED}+${RESET}"
jq -r '
  .entry
  | (length) as $n
  | if $n == 0 then empty
    else [.[0], .[($n/2 | floor)], .[-1]] end
  | .[]
  | .resource
  | . as $r
  | ($r.content[0].attachment.data | @base64d | gsub("\r"; "")) as $nota
  | "",
    "  [96m▶ \($r.date[0:10])[0m",
    "    [2m" + (
      ($nota | split("# History of Present Illness\n")[1] // $nota)
      | split("\n\n")[0]
      | gsub("\n"; " ")
      | gsub("  +"; " ")
      | .[0:240] + "..."
    ) + "[0m"
' /tmp/bundle_notas.json

pausa 5

separador

# CENA 5 — FECHAMENTO
cat <<EOF
${BOLD}Parâmetros do \$everything que mudam o jogo:${RESET}

  ${CYAN}_type${RESET}       filtra tipos de recurso
  ${CYAN}_since${RESET}      apenas modificados depois de data X
  ${CYAN}start/end${RESET}   janela clínica (encounter, internação)
  ${CYAN}_count${RESET}      controla paginação

${DIM}Código completo: link nos comentários${RESET}

EOF
pausa 4

separador

# CENA 6 — TABELA COMPARATIVA FINAL
export LC_NUMERIC=en_US.UTF-8
TOKENS_SAVED=$((CRU_TOKENS - FIL_TOKENS))
BYTES_SAVED_KB=$(awk "BEGIN {printf \"%.0f\", ($CRU_BYTES - $FIL_BYTES)/1024}")

echo -e "${BOLD}${CYAN}┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓${RESET}"
echo -e "${BOLD}${CYAN}┃${RESET}  ${BOLD}IMPACTO DO _type NO CONSUMO${RESET}                          ${BOLD}${CYAN}┃${RESET}"
echo -e "${BOLD}${CYAN}┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛${RESET}"
echo ""
printf "  %-14s    ${BOLD}${RED}%17s${RESET}    ${BOLD}${GREEN}%17s${RESET}\n" "" "SEM _type" "COM _type"
printf "  %-14s    ${DIM}%17s${RESET}    ${DIM}%17s${RESET}\n" "" "─────────────────" "─────────────────"
printf "  ${BOLD}%-14s${RESET}    %'14d KB    %'14d KB\n" "Tamanho" "$(awk "BEGIN{print int($CRU_BYTES/1024)}")" "$(awk "BEGIN{print int($FIL_BYTES/1024)}")"
printf "  ${BOLD}%-14s${RESET}    %'17d    %'17d\n" "Entries" "$CRU_ENTRIES" "$FIL_ENTRIES"
printf "  ${BOLD}%-14s${RESET}    %'17d    %'17d\n" "Tokens (~)" "$CRU_TOKENS" "$FIL_TOKENS"
echo ""
printf "  ${BOLD}${GREEN}▼ Economia:${RESET}  %'d tokens  ${BOLD}${GREEN}(-${REDUCAO}%%)${RESET}\n" "$TOKENS_SAVED"
printf "  ${DIM}             %'d KB de bundle${RESET}\n" "$BYTES_SAVED_KB"
echo ""
pausa 6
